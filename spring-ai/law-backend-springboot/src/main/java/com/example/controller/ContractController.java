package com.example.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.netty.handler.ssl.SslContextBuilder;
import io.netty.handler.ssl.util.InsecureTrustManagerFactory;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import reactor.netty.http.client.HttpClient;

import javax.net.ssl.SSLException;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import java.util.Date;
import java.util.Set;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import io.jsonwebtoken.security.Keys;
import javax.crypto.SecretKey;
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ContractController {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final WebClient webClient;

    public ContractController() {
        try {
            String endpoint = "http://langchainagent-app:8000/contracts_explanation/stream";
            boolean useHttps = endpoint != null && endpoint.startsWith("https");

            final HttpClient httpClient;
            if (useHttps) {
                httpClient = HttpClient.create()
                        .secure(spec -> {
                            try {
                                spec.sslContext(
                                        SslContextBuilder.forClient()
                                                .trustManager(InsecureTrustManagerFactory.INSTANCE)
                                                .build()
                                );
                            } catch (SSLException e) {
                                throw new RuntimeException(e);
                            }
                        });
            } else {
                httpClient = HttpClient.create();
            }

            this.webClient = WebClient.builder()
                    .clientConnector(new ReactorClientHttpConnector(httpClient))
                    // ✅ 解决 256KB 限制
                    .codecs(configurer ->
                            configurer.defaultCodecs()
                                    .maxInMemorySize(10 * 1024 * 1024)
                    )
                    .build();

        } catch (Exception e) {
            throw new RuntimeException("WebClient init error", e);
        }
    }

    @PostMapping("/contract_analysis_stream")
    public SseEmitter analyzeContract(@RequestBody Map<String, Object> payload) {

        SseEmitter emitter = new SseEmitter(0L);

        ExecutorService executor = Executors.newSingleThreadExecutor();
        ScheduledExecutorService heartbeat = Executors.newSingleThreadScheduledExecutor();
        AtomicBoolean closed = new AtomicBoolean(false);

        executor.submit(() -> {

            CountDownLatch latch = new CountDownLatch(1);



            try {
                // 1. 生成 JWT 作为 thread_id
                // 密钥必须至少32字节（256位），建议用环境变量注入
                SecretKey key = Keys.secretKeyFor(SignatureAlgorithm.HS256);

                String threadIdJwt = Jwts.builder()
                        .setSubject("thread")
                        .signWith(key) // 算法会自动匹配密钥强度
                        .compact();

                // 2. 先把 JWT 发送给前端
                emitter.send(SseEmitter.event().data(Map.of("type", "thread_id", "thread_id", threadIdJwt), MediaType.APPLICATION_JSON));

                // 3. 心跳
                heartbeat.scheduleAtFixedRate(() -> {
                    if (!closed.get()) {
                        try {
                            emitter.send(":\n\n");
                        } catch (Exception ignored) {}
                    }
                }, 15, 15, TimeUnit.SECONDS);

                Map<String, Object> requestBody = Map.of(
                        "input", Map.of("input", payload.get("input")),
                        "config", Map.of(
                                "configurable", Map.of(
                                        "thread_id", threadIdJwt,
                                        "recursion_limit", 50
                                )
                        ),
                        "kwargs", Map.of()
                );

                StringBuilder buffer = new StringBuilder();
                Set<String> processedContents = ConcurrentHashMap.newKeySet();

                webClient.post()
                    .uri(llmEndpoint())
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.TEXT_EVENT_STREAM)
                        .bodyValue(requestBody)

                        .retrieve()
                        .bodyToFlux(DataBuffer.class)

                        .map(dataBuffer -> {
                            byte[] bytes = new byte[dataBuffer.readableByteCount()];
                            dataBuffer.read(bytes);
                            DataBufferUtils.release(dataBuffer);
                            return new String(bytes, StandardCharsets.UTF_8);
                        })

                        .subscribe(

                                // ✅ 核心修复：逐行解析 + 半包拼接
                                chunk -> {
                                    try {

                                        buffer.append(chunk);

                                        String all = buffer.toString();

                                        int index;
                                        while ((index = all.indexOf("\n")) != -1) {

                                            String line = all.substring(0, index).trim();
                                            all = all.substring(index + 1);

                                            if (line.isEmpty()) continue;
                                            if (line.startsWith(":")) continue;
                                            if (line.startsWith("event:")) continue;
                                            if (!line.startsWith("data:")) continue;

                                            String json = line.substring(5).trim();

                                            if (json.isBlank() || "[DONE]".equals(json)) continue;

                                            System.out.println("✅ JSON: " + json);

                                            Map<String, Object> root =
                                                    objectMapper.readValue(json, Map.class);

                                            Map<String, Object> output =
                                                    (Map<String, Object>) root.get("output");

                                            if (output != null) {

                                                String response = (String) output.get("response");

                                                if (response != null && !response.isBlank()) {
                                                    if (processedContents.add(response)) {
                                                        sendData(emitter, response);
                                                    }
                                                }
                                            }

                                            // step 信息
                                            String step = (String) root.get("step");
                                            if (step != null) {
                                                String content = step;
                                                if (processedContents.add(content)) {
                                                    sendData(emitter, content);
                                                }
                                            }
                                        }

                                        // ✅ 半包保留
                                        buffer.setLength(0);
                                        buffer.append(all);

                                    } catch (Exception e) {
                                        System.err.println("❌ 解析异常");
                                        e.printStackTrace();
                                    }
                                },

                                // ❌ 异常 — 将错误信息通过 SSE 返回给客户端以便调试
                                error -> {
                                    error.printStackTrace();
                                    String errMsg = error.getMessage();
                                    if (errMsg == null || errMsg.isBlank()) errMsg = error.toString();
                                    try {
                                        sendError(emitter, "服务异常: " + errMsg);
                                    } catch (Exception ignored) {}
                                    cleanup(closed, heartbeat, latch);
                                    emitter.complete();
                                },

                                // ✅ 完成
                                () -> {
                                    sendDone(emitter, "【回答完成】");
                                    cleanup(closed, heartbeat, latch);
                                    emitter.complete();
                                }
                        );

                latch.await();

            } catch (Exception e) {
                e.printStackTrace();
                sendError(emitter, "系统异常");
                emitter.complete();
                cleanup(closed, heartbeat, latch);
            } finally {
                executor.shutdown();
            }
        });

        emitter.onCompletion(() -> {
            closed.set(true);
            heartbeat.shutdown();
        });

        emitter.onTimeout(() -> {
            closed.set(true);
            heartbeat.shutdown();
        });

        return emitter;
    }

    private void cleanup(AtomicBoolean closed, ScheduledExecutorService heartbeat, CountDownLatch latch) {
        closed.set(true);
        heartbeat.shutdown();
        latch.countDown();
    }


    private void sendData(SseEmitter emitter, String content) {
        try {
            emitter.send(
                    SseEmitter.event()
                            .data(Map.of("type", "data", "content", content), MediaType.APPLICATION_JSON)
            );
        } catch (Exception e) {
            emitter.complete();
        }
    }

    private void sendDone(SseEmitter emitter, String content) {
        try {
            emitter.send(
                    SseEmitter.event()
                            .data(Map.of("type", "done", "content", content), MediaType.APPLICATION_JSON)
            );
        } catch (Exception e) {
            emitter.complete();
        }
    }

    private void sendError(SseEmitter emitter, String content) {
        try {
            emitter.send(
                    SseEmitter.event()
                            .data(Map.of("type", "error", "content", content), MediaType.APPLICATION_JSON)
            );
        } catch (Exception e) {
            emitter.complete();
        }
    }

    private String llmEndpoint() {
        String env = System.getenv("LLM_ENDPOINT");
        if (env == null || env.isEmpty()) {
            return "http://langchainagent-app:8000/contracts_explanation/stream";
        }
        return env;
    }
}