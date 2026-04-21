package com.example.filter;

import com.example.util.JwtUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;

public class JwtAuthenticationFilter extends OncePerRequestFilter {

   private final JwtUtil jwtUtil;

   @Value("${jwt.header:Authorization}")
   private String headerName;

   @Value("${jwt.prefix:Bearer }")
   private String tokenPrefix;

   private static final List<String> EXCLUDED_PATHS = Arrays.asList(
           "/api/auth/login",
           "/api/auth/register",
           "/actuator/health",
           "/actuator/info"
   );

   public JwtAuthenticationFilter(JwtUtil jwtUtil) {
       this.jwtUtil = jwtUtil;
   }

   @Override
   protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
           throws ServletException, IOException {

       String path = request.getRequestURI();

       if (EXCLUDED_PATHS.stream().anyMatch(path::startsWith)) {
           filterChain.doFilter(request, response);
           return;
       }

       String authHeader = request.getHeader(headerName != null ? headerName : "Authorization");

       if (authHeader == null || tokenPrefix == null || !authHeader.startsWith(tokenPrefix)) {
           response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
           response.setContentType("application/json;charset=UTF-8");
           response.getWriter().write("{\"error\": \"缺少或无效的Authorization头\"}");
           return;
       }

       String token = authHeader.substring(tokenPrefix.length());

       if (!jwtUtil.validateToken(token)) {
           response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
           response.setContentType("application/json;charset=UTF-8");
           response.getWriter().write("{\"error\": \"Token无效或已过期\"}");
           return;
       }

       String username = jwtUtil.getUsernameFromToken(token);
       request.setAttribute("username", username);

       filterChain.doFilter(request, response);
   }
}
