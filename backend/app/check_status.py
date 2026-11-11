from .api_client import ApiFootballClient, requests_used_today


def main() -> None:
    client = ApiFootballClient()
    status = client.get("/status")
    api_side = status.get("requests", {})
    print("Plan:", status.get("subscription", {}).get("plan"))
    print("API says:", api_side)
    print("Our counter (UTC today):", requests_used_today())
    print("Remaining header on last response:", client.requests_remaining)


if __name__ == "__main__":
    main()