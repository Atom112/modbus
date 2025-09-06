package com.example.gpsbackend;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;

@RestController
public class GpsController {

    private final GpsService gpsService;

    @Autowired
    public GpsController(GpsService gpsService) {
        this.gpsService = gpsService;
    }

    /**
     * 监听来自Python脚本的连接测试（GET /）。
     * 返回一个简单的成功消息。
     */
    @GetMapping("/")
    public String home() {
        System.out.println("收到来自Python的HTTP连接测试请求。");
        return "Spring Boot Backend is running!";
    }

    /**
     * 接收Python脚本发送的GPS数据（POST /api/gps_data）。
     * 并将接收到的数据打印到控制台。
     */
    @PostMapping("/api/gps_data")
    public ResponseEntity<String> receiveGpsData(@RequestBody GpsData gpsData) {
        System.out.println("\n**************************************************");
        System.out.println(" 收到来自Python的GPS数据:");
        System.out.println(" 纬度 (Latitude):" + gpsData.getLatitude());
        System.out.println(" 经度 (Longitude):" + gpsData.getLongitude());
        System.out.println(" 设备ID (Device ID):" + gpsData.getDevice_id());
        System.out.println(" 时间戳 (Timestamp):" + String.format("%.6f", gpsData.getTimestamp()));
        System.out.println(" >**************************************************\n");

        return new ResponseEntity<>("GPS数据接收成功！", HttpStatus.OK);
    }
}