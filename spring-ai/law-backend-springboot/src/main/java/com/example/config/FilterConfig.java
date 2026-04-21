package com.example.config;

import com.example.filter.JwtAuthenticationFilter;
import com.example.util.JwtUtil;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FilterConfig {

   @Bean
   public JwtAuthenticationFilter jwtAuthenticationFilter(JwtUtil jwtUtil) {
       return new JwtAuthenticationFilter(jwtUtil);
   }

   @Bean
   public FilterRegistrationBean<JwtAuthenticationFilter> jwtFilterRegistration(JwtAuthenticationFilter jwtFilter) {
       FilterRegistrationBean<JwtAuthenticationFilter> registration = new FilterRegistrationBean<>();
       registration.setFilter(jwtFilter);
       registration.addUrlPatterns("/api/*");
       registration.setName("jwtAuthenticationFilter");
       registration.setOrder(1);
       return registration;
   }
}
