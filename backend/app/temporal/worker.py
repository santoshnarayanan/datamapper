import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

# ✅ NEW imports (Phase 6 system)
from app.temporal.workflows import DataPreparationWorkflow
from app.temporal.activities import apply_step_activity


# 🔥 Retry connection to Temporal
async def connect_temporal():
    while True:
        try:
            print("⏳ Connecting to Temporal at localhost:7233...")
            client = await Client.connect("localhost:7233")
            print("✅ Connected to Temporal!")
            return client
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("🔁 Retrying in 3 seconds...\n")
            await asyncio.sleep(3)


async def main():
    client = await connect_temporal()

    worker = Worker(
        client,
        task_queue="data-prepare-queue",   # ✅ IMPORTANT
        workflows=[DataPreparationWorkflow],
        activities=[apply_step_activity],
    )

    print("🚀 Worker started (Phase 7 system)...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())