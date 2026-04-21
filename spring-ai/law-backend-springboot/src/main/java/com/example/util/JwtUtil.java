package com.example.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component
public class JwtUtil {

   @Value("${jwt.secret}")
   private String secret;

   @Value("${jwt.expiration}")
   private Long expiration;

   private SecretKey getSigningKey() {
       byte[] keyBytes = secret.getBytes(StandardCharsets.UTF_8);
       return Keys.hmacShaKeyFor(keyBytes);
   }

   public String generateToken(String username) {
       Map<String, Object> claims = new HashMap<>();
       return createToken(claims, username);
   }

   private String createToken(Map<String, Object> claims, String subject) {
       Date now = new Date();
       Date expirationDate = new Date(now.getTime() + expiration);

       return Jwts.builder()
               .setClaims(claims)
               .setSubject(subject)
               .setIssuedAt(now)
               .setExpiration(expirationDate)
               .signWith(getSigningKey(), SignatureAlgorithm.HS256)
               .compact();
   }

   public String getUsernameFromToken(String token) {
       Claims claims = getAllClaimsFromToken(token);
       return claims.getSubject();
   }

   public boolean validateToken(String token) {
       try {
           getAllClaimsFromToken(token);
           return !isTokenExpired(token);
       } catch (Exception e) {
           return false;
       }
   }

   private boolean isTokenExpired(String token) {
       Date expiration = getExpirationDateFromToken(token);
       return expiration.before(new Date());
   }

   private Date getExpirationDateFromToken(String token) {
       Claims claims = getAllClaimsFromToken(token);
       return claims.getExpiration();
   }

   private Claims getAllClaimsFromToken(String token) {
       return Jwts.parserBuilder()
               .setSigningKey(getSigningKey())
               .build()
               .parseClaimsJws(token)
               .getBody();
   }
}
