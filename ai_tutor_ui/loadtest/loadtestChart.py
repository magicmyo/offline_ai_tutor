import pandas as pd
import matplotlib.pyplot as plt

#modlename = 'Tinyllama-1.1b'
#fprefix = 'tiny'

#modlename = 'Qwen2.5-3b'
#fprefix = 'qwen25'

#modlename = 'Mistral-7b'
#fprefix = 'mistral'

modlename = 'Meta-Llama-3-8B'
fprefix = 'meta'


fname = fprefix+'_load_test_results.csv'
# Load data
df = pd.read_csv(fname)

# Separate by user count
df_2 = df[df['users'] == 2]
df_4 = df[df['users'] == 4]

# Failure Percent vs Total Requests
plt.figure(figsize=(8,6))
plt.plot(df_2['total_requests'], df_2['failure_percent'], marker='o', label='2 users')
plt.plot(df_4['total_requests'], df_4['failure_percent'], marker='o', linestyle='-.', label='4 users') # dot-line
plt.xlabel('Total Requests')
plt.ylabel('Failure Percentage (%)')
plt.title(modlename+': Failure Percentage vs Total Requests by User Count')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(fprefix+'_failure_vs_requests_dotline.jpg')
plt.show()

# Throughput vs Total Requests
plt.figure(figsize=(8,6))
plt.plot(df_2['total_requests'], df_2['throughput_req_per_sec'], marker='o', label='2 users')
plt.plot(df_4['total_requests'], df_4['throughput_req_per_sec'], marker='o', linestyle='-.', label='4 users') # dot-line
plt.xlabel('Total Requests')
plt.ylabel('Throughput (req/sec)')
plt.title(modlename+': Throughput vs Total Requests by User Count')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(fprefix+'_throughput_vs_requests_dotline.jpg')
plt.show()
