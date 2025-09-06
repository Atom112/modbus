package com.example.gpsbackend;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener; // 仍然保留，但不再用于触发初始请求
import org.springframework.scheduling.annotation.Scheduled; // 导入 Scheduled
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;

@Service
public class GpsService {

    // 从application.properties中读取Python Flask应用的URL
    @Value("${python.flask.url}")
    private String pythonFlaskUrl;

    private final RestTemplate restTemplate;

    public GpsService() {
        // 初始化RestTemplate用于HTTP通信
        this.restTemplate = new RestTemplate();
    }

    /**
     * **<font color="#36393b">每五秒调用一次此方法，向Python脚本发送请求。</font>**
     * **<font color="#36393b">initialDelay: 启动后首次执行的延迟时间 (毫秒)。</font>**
     * **<font color="#36393b">fixedRate: 固定速率执行，两次任务开始时间间隔 (毫秒)。</font>**
     */
    @Scheduled(initialDelay = 5000, fixedRate = 5000) // **<font color="#9a031e">首次执行延迟5秒，之后每5秒执行一次</font>**
    public void sendRequestToPythonPeriodically() {
        System.out.println(" **<font color=\"#9A031E\">定时任务触发：准备向Python请求GPS数据...</font>** ");
        triggerPythonGpsCollection();
    }

    /**
     * **<font color="#36393b">向Python Flask应用发送POST请求，通知其开始收集GPS数据。</font>**
     */
    public void triggerPythonGpsCollection() {
        // 根据您Python脚本中定义的监听路径，这里拼接到 /notify_request_received
        String url = pythonFlaskUrl + "/notify_request_received";
        System.out.println(" **<font color=\"#0056b3\">正在发送请求到Python Flask应用:</font>** " + url);
        try {
            // 向Python Flask应用的 /notify_request_received 路径发送一个空的POST请求
            // Python脚本中的 /notify_request_received 路由接受 POST 或 GET 请求
            ResponseEntity<String> response = restTemplate.postForEntity(url, null, String.class);
            System.out.println(" **<font color=\"#0000FF\">已向Python发送GPS数据收集请求。</font>** 响应状态码: " + response.getStatusCode());
            System.out.println(" **<font color=\"#0000FF\">响应体:</font>** " + response.getBody());
        } catch (Exception e) {
            System.err.println(" **<font color=\"#FF0000\">向Python发送GPS数据收集请求失败:</font>** " + e.getMessage());
        }
    }

    // 您可以根据需要保留或删除此方法，如果不需要在应用启动后立即进行一次性请求，则可以删除。
    // 如果需要确保应用启动后立即发送一次，而不是等待initialDelay，可以保留，但逻辑上可能会有轻微重复。
    // @EventListener(ApplicationReadyEvent.class)
    // public void sendInitialRequestOnStartup() {
    //     System.out.println("Spring Boot应用程序已启动。准备向Python请求GPS数据...");
    //     triggerPythonGpsCollection();
    // }
}