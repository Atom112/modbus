package com.example.gpsbackend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling; // 导入 EnableScheduling

@SpringBootApplication
@EnableScheduling // **<font color="#9a031e">启用Spring Boot的定时任务调度功能</font>**
public class GpsbackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(GpsbackendApplication.class, args);
    }

}