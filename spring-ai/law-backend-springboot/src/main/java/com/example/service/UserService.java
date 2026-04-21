package com.example.service;

import com.example.entity.User;
import com.example.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Optional;

@Service
public class UserService {

   private final UserRepository userRepository;

   @Autowired
   public UserService(UserRepository userRepository) {
       this.userRepository = userRepository;
   }

   public Optional<User> findByName(String name) {
       return userRepository.findByName(name);
   }

   public boolean validatePassword(String rawPassword, String encodedPassword) {
       return rawPassword.equals(encodedPassword);
   }

   public User saveUser(User user) {
       return userRepository.save(user);
   }

   public boolean existsByName(String name) {
       return userRepository.existsByName(name);
   }
}
