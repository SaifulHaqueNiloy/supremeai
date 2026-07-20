package com.supremeai.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * বাংলা মন্তব্য: TaskProcessingService.processAsync()-এর জন্য bounded thread pool।
 * সাইজ env-var দিয়ে override করা যায় যাতে কোনো hardcode ছাড়াই ডিপ্লয়মেন্ট
 * অনুযায়ী টিউন করা যায় (Zero Hardcode principle)।
 */
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "taskExecutor")
    public Executor taskExecutor(
            org.springframework.core.env.Environment env
    ) {
        int coreSize = Integer.parseInt(env.getProperty("TASK_EXECUTOR_CORE_SIZE", "5"));
        int maxSize = Integer.parseInt(env.getProperty("TASK_EXECUTOR_MAX_SIZE", "20"));
        int queueCapacity = Integer.parseInt(env.getProperty("TASK_EXECUTOR_QUEUE_CAPACITY", "500"));

        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(coreSize);
        executor.setMaxPoolSize(maxSize);
        executor.setQueueCapacity(queueCapacity);
        executor.setThreadNamePrefix("task-exec-");
        executor.initialize();
        return executor;
    }
}
