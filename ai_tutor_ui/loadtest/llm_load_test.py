import requests
import threading
import time
import csv
import matplotlib.pyplot as plt

# Test configuration
#URL = "http://127.0.0.1:8081/v1/chat/completions"
URL = "http://172.18.0.1:8081/v1/chat/completions"
PAYLOAD = {"messages": [{"role": "user", "content": "Explain Newton's second law in a paragraph suitable for high-school students."}], "model": "test-model"}  # Customize as needed
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 60  # sec

# Parameters
concurrent_users_list = [2, 4]
total_requests_list = [4, 8, 12]  # Aligned total_request values for both 2 and 4 users

results = []

def worker(user_id, requests_count, thread_results):
    successes = 0
    failures = 0
    start_time = time.time()
    for _ in range(requests_count):
        try:
            resp = requests.post(URL, json=PAYLOAD, timeout=TIMEOUT)
            if resp.ok:
                successes += 1
            else:
                failures += 1
        except Exception:
            failures += 1
    end_time = time.time()
    elapsed = end_time - start_time
    print({"successes": successes, "failures": failures, "elapsed": elapsed})
    thread_results.append({"successes": successes, "failures": failures, "elapsed": elapsed})

for users in concurrent_users_list:
    for total_requests in total_requests_list:
        if total_requests % users != 0:
            continue  # Only process cases where req_per_user is integer
        req_per_user = total_requests // users
        thread_results = []
        threads = []
        for i in range(users):
            thread = threading.Thread(target=worker, args=(i, req_per_user, thread_results))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        total_success = sum(r["successes"] for r in thread_results)
        total_failure = sum(r["failures"] for r in thread_results)
        total_elapsed = max(r["elapsed"] for r in thread_results)  # Take max time (worst case)
        throughput = total_requests / total_elapsed if total_elapsed > 0 else 0
        percentage_failure = (total_failure / total_requests) * 100.0 if total_requests > 0 else 0
        result = {
            "users": users,
            "request_per_user": req_per_user,
            "throughput_req_per_sec": throughput,
            "total_failure": total_failure,
            "total_requests": total_requests,
            "failure_percent": percentage_failure,
        }
        results.append(result)
        print(result)

# Write to CSV
with open("load_test_results.csv", "w", newline="") as csvfile:
    fieldnames = ["users", "request_per_user", "throughput_req_per_sec", "total_failure", "total_requests", "failure_percent"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

# Graph: Throughput vs Total Requests (group by users)
# for users in concurrent_users_list:
#     x = [r["total_requests"] for r in results if r["users"] == users]
#     y = [r["throughput_req_per_sec"] for r in results if r["users"] == users]
#     plt.plot(x, y, marker="o", label=f"{users} users")
# plt.xlabel("Total Requests")
# plt.ylabel("Throughput (req/sec)")
# plt.title("Throughput vs Total Requests by User Count")
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.savefig("throughput_vs_requests.png")
# plt.show()

# Graph: Failure Percent vs Total Requests
# plt.figure()
# for users in concurrent_users_list:
#     x = [r["total_requests"] for r in results if r["users"] == users]
#     y = [r["failure_percent"] for r in results if r["users"] == users]
#     plt.plot(x, y, marker="o", label=f"{users} users")
# plt.xlabel("Total Requests")
# plt.ylabel("Failure Percentage (%)")
# plt.title("Failure Percentage vs Total Requests by User Count")
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.savefig("failure_vs_requests.png")
# plt.show()
