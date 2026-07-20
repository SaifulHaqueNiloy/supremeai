package com.supremeai.tasks;

import com.supremeai.models.TaskEntity;

/**
 * বাংলা মন্তব্য: প্রতিটি task_type-এর জন্য একটি পৃথক handler ইমপ্লিমেন্ট করতে হবে।
 * এই ইন্টারফেসটি ছাড়া আগে submitTask() শুধু DB-তে QUEUED সেভ করে থামত — কোনো
 * প্রকৃত প্রসেসিং কখনো শুরুই হতো না (silent hang, কোনো error ছাড়াই)।
 * এখন প্রতিটি নিবন্ধিত (registered) TaskHandler bean স্বয়ংক্রিয়ভাবে
 * TaskProcessingService দ্বারা wiring হয়ে যাবে।
 */
public interface TaskHandler {

    /** এই handler কোন task_type প্রসেস করে। */
    String getTaskType();

    /**
     * প্রকৃত কাজ সম্পন্ন করে। এক্সেপশন থ্রো করলে TaskProcessingService স্বয়ংক্রিয়ভাবে
     * task-কে FAILED মার্ক করবে এবং errorMessage সেভ করবে।
     */
    String handle(TaskEntity task) throws Exception;
}
