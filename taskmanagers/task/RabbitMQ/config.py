RABBITMQ_SERVER_TOPOLOGY = {
    "exchanges": {
        "events": {
            "name": "events.topic",
            "type": "topic"
        },
        "jobs": {
            "name": "jobs.direct",
            "type": "direct"
        }
    },

    "queues": {
        "message": {
            "name": "message.queue"
        },
        "jobs": {
            "name": "jobs.queue"
        }
    },

    "routes": {
        "MESSAGE_SEND": {
            "exchange": "events",
            "queue": "message",
            "routing_key": "message.send"
        },
        "MESSAGE_RETRY": {
            "exchange": "events",
            "queue": "message",
            "routing_key": "message.retry"
        },
        "JOB_RUN": {
            "exchange": "jobs",
            "queue": "jobs",
            "routing_key": "job.run"
        }
    }
}