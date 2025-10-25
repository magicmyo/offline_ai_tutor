import pandas as pd
import matplotlib.pyplot as plt

# Load CSVs (ensure filenames match)
df_meta = pd.read_csv('meta_load_test_results.csv')
df_mistral = pd.read_csv('mistral_load_test_results.csv')
df_qwen25 = pd.read_csv('qwen25_load_test_results.csv')
df_tiny = pd.read_csv('tiny_load_test_results.csv')

plt.figure(figsize=(10,6))

# Use different linestyles and markers for black & white visibility
plt.plot(df_meta['users'], df_meta['throughput_req_per_sec'],
         marker='o', linestyle='-', label='Meta-Llama-3-8b')            # solid
plt.plot(df_mistral['users'], df_mistral['throughput_req_per_sec'],
         marker='s', linestyle='--', label='Mistral-7b')        # dashed
plt.plot(df_qwen25['users'], df_qwen25['throughput_req_per_sec'],
         marker='^', linestyle=':', label='Qwen2.5-3b')        # dotted
plt.plot(df_tiny['users'], df_tiny['throughput_req_per_sec'],
         marker='D', linestyle='-.', label='Tinyllama-1.1b')           # dash-dot

plt.xlabel('Number of Users')
plt.ylabel('Throughput (req/sec)')
plt.title('Throughput vs Users for Each Model')
plt.legend()
plt.grid(True, linestyle=':')
plt.tight_layout()

# Save as black-and-white friendly image
plt.savefig('load_test_comparison_bw.png', dpi=300)
plt.show()
