package com.example.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "user")
public class User {

   @Id
   @GeneratedValue(strategy = GenerationType.IDENTITY)
   private Long id;

   @Column(name = "name", nullable = false, unique = true, length = 50)
   private String name;

   @Column(nullable = false, length = 100)
   private String password;

   @Column(name = "create_time")
   private LocalDateTime createTime;

   @Column(name = "update_time")
   private LocalDateTime updateTime;

   public User() {
   }

   public Long getId() {
       return id;
   }

   public void setId(Long id) {
       this.id = id;
   }

   public String getName() {
       return name;
   }

   public void setName(String name) {
       this.name = name;
   }

   public String getPassword() {
       return password;
   }

   public void setPassword(String password) {
       this.password = password;
   }

   public LocalDateTime getCreateTime() {
       return createTime;
   }

   public void setCreateTime(LocalDateTime createTime) {
       this.createTime = createTime;
   }

   public LocalDateTime getUpdateTime() {
       return updateTime;
   }

   public void setUpdateTime(LocalDateTime updateTime) {
       this.updateTime = updateTime;
   }

   @PrePersist
   protected void onCreate() {
       createTime = LocalDateTime.now();
       updateTime = LocalDateTime.now();
   }

   @PreUpdate
   protected void onUpdate() {
       updateTime = LocalDateTime.now();
   }
}
