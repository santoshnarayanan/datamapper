import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from temporal_worker.workflows import HelloWorkflow
from temporal_worker.activities import say_hello


async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="hello-task-queue",
        workflows=[HelloWorkflow],
        activities=[say_hello],
    )

    print("Worker started...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())