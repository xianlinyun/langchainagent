# Multi-stage build for Spring Boot law-backend-springboot

# 1. Build stage
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app

# 先复制 Maven 配置（如有 settings.xml）和 pom.xml，利用 Docker 层缓存依赖
COPY settings.xml /app/settings.xml
COPY pom.xml .

# 预下载依赖，后续代码变更不会触发重复下载（除非 pom.xml/settings.xml 变了）
RUN mvn -B -s /app/settings.xml -Dmaven.test.skip=true dependency:go-offline

# 再复制源码
COPY src ./src

# 构建可执行 jar
RUN mvn -B -s /app/settings.xml -Dmaven.test.skip=true package

# 2. Runtime stage
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# Copy packaged jar from build stage
COPY --from=build /app/target/law-backend-springboot-0.0.1-SNAPSHOT.jar app.jar

# Match server.port=8080 in application.yml
EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
