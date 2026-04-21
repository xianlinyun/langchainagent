package com.example.controller;

import com.example.dto.LoginRequest;
import com.example.dto.LoginResponse;
import com.example.dto.RegisterRequest;
import com.example.dto.RegisterResponse;
import com.example.entity.User;
import com.example.service.UserService;
import com.example.util.JwtUtil;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {

   private final JwtUtil jwtUtil;
   private final UserService userService;

   public AuthController(JwtUtil jwtUtil, UserService userService) {
       this.jwtUtil = jwtUtil;
       this.userService = userService;
   }

   @PostMapping("/login")
   public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest loginRequest) {
       if (loginRequest.getUsername() == null || loginRequest.getPassword() == null) {
           return ResponseEntity.badRequest().body(new LoginResponse(null, null, "用户名和密码不能为空"));
       }

       Optional<User> userOpt = userService.findByName(loginRequest.getUsername());

       if (userOpt.isEmpty() || !userService.validatePassword(loginRequest.getPassword(), userOpt.get().getPassword())) {
           return ResponseEntity.status(401).body(new LoginResponse(null, null, "用户名或密码错误"));
       }

       User user = userOpt.get();
       String token = jwtUtil.generateToken(user.getName());
       return ResponseEntity.ok(new LoginResponse(token, user.getName(), "登录成功"));
   }

   @PostMapping("/register")
   public ResponseEntity<RegisterResponse> register(@RequestBody RegisterRequest registerRequest) {
       if (registerRequest.getUsername() == null || registerRequest.getUsername().trim().isEmpty()) {
           return ResponseEntity.badRequest().body(new RegisterResponse(null, null, "用户名不能为空"));
       }

       if (registerRequest.getPassword() == null || registerRequest.getPassword().length() < 6) {
           return ResponseEntity.badRequest().body(new RegisterResponse(null, null, "密码不能为空且至少6位"));
       }

       if (userService.existsByName(registerRequest.getUsername())) {
           return ResponseEntity.badRequest().body(new RegisterResponse(null, null, "用户名已存在"));
       }

       User user = new User();
       user.setName(registerRequest.getUsername());
       user.setPassword(registerRequest.getPassword());

       User savedUser = userService.saveUser(user);

       return ResponseEntity.ok(new RegisterResponse(savedUser.getId(), savedUser.getName(), "注册成功"));
   }

   @PostMapping("/verify")
   public ResponseEntity<?> verifyToken(@RequestHeader("Authorization") String authHeader) {
       if (authHeader == null || !authHeader.startsWith("Bearer ")) {
           return ResponseEntity.status(401).body("无效的Token");
       }

       String token = authHeader.substring(7);
       if (jwtUtil.validateToken(token)) {
           String username = jwtUtil.getUsernameFromToken(token);
           return ResponseEntity.ok(new LoginResponse(token, username, "Token有效"));
       } else {
           return ResponseEntity.status(401).body("Token无效或已过期");
       }
   }
}
