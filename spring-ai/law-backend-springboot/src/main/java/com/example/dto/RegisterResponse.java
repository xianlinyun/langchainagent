package com.example.dto;

public class RegisterResponse {
   private Long id;
   private String username;
   private String message;

   public RegisterResponse() {
   }

   public RegisterResponse(Long id, String username, String message) {
       this.id = id;
       this.username = username;
       this.message = message;
   }

   public Long getId() {
       return id;
   }

   public void setId(Long id) {
       this.id = id;
   }

   public String getUsername() {
       return username;
   }

   public void setUsername(String username) {
       this.username = username;
   }

   public String getMessage() {
       return message;
   }

   public void setMessage(String message) {
       this.message = message;
   }
}
