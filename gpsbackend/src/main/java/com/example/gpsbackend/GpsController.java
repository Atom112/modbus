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
     * **<font color="#36393b">监听来自Python脚本的连接测试（GET /）。</font>**
     * **<font color="#36393b">返回一个简单的成功消息。</font>**
     */
    @GetMapping("/")
    public String home() {
        System.out.println(" **<font color=\"#0000FF\">收到来自Python的HTTP连接测试请求。</font>** ");
        return "Spring Boot Backend is running!";
    }

    /**
     * **<font color="#36393b">接收Python脚本发送的GPS数据（POST /api/gps_data）。</font>**
     * **<font color="#36393b">并将接收到的数据打印到控制台。</font>**
     */
    @PostMapping("/api/gps_data")
    public ResponseEntity<String> receiveGpsData(@RequestBody GpsData gpsData) {
        System.out.println("\n **<font color=\"#F5B041\">**************************************************</font>** ");
        System.out.println(" **<font color=\"#1ABC9C\">收到来自Python的GPS数据:</font>** ");
        System.out.println("  **<font color=\"#3498DB\">纬度 (Latitude):</font>** " + gpsData.getLatitude());
        System.out.println("  **<font color=\"#3498DB\">经度 (Longitude):</font>** " + gpsData.getLongitude());
        System.out.println("  **<font color=\"#3498DB\">设备ID (Device ID):</font>** " + gpsData.getDevice_id());
        System.out.println("  **<font color=\"#3498DB\">时间戳 (Timestamp):</font>** " + String.format("%.6f", gpsData.getTimestamp()));
        System.out.println(" **<font color=\"#F5B041\">**************************************************</font>** \n");

        return new ResponseEntity<>("GPS数据接收成功！", HttpStatus.OK);
    }
}