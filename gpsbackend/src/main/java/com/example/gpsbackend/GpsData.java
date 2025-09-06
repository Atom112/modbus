package com.example.gpsbackend;

import lombok.Data; // 自动生成getter, setter, equals, hashCode, toString方法

/**
 * 用于接收从Python脚本发送的GPS数据的DTO（数据传输对象）。
 */
@Data
public class GpsData {
    private Double latitude;
    private Double longitude;
    private String device_id;
    private Double timestamp; // Python的time.time()返回浮点数，因此这里使用Double
}