import pandas as pd
import matplotlib.pyplot as plt

# Load CSVs
df_meta = pd.read_csv('meta_load_test_results.csv')
df_mistral = pd.read_csv('mistral_load_test_results.csv')
df_qwen25 = pd.read_csv('qwen25_load_test_results.csv')
df_tiny = pd.read_csv('tiny_load_test_results.csv')

plt.figure(figsize=(10,6))

# Different linestyles for black & white printing
plt.plot(df_meta['users'], df_meta['failure_percent'], marker='o', linestyle='-', label='Meta-Llama-3-8b')           # solid
plt.plot(df_mistral['users'], df_mistral['failure_percent'], marker='s', linestyle='--', label='Mistral-7b') # dashed
plt.plot(df_qwen25['users'], df_qwen25['failure_percent'], marker='^', linestyle=':', label='Qwen2.5-3b')   # dotted
plt.plot(df_tiny['users'], df_tiny['failure_percent'], marker='D', linestyle='-.', label='Tinyllama-1.1b')          # dash-dot

plt.xlabel('Number of Users')
plt.ylabel('Failure Percent')
plt.title('Failure Percent vs Users for Each Model')
plt.legend()
plt.grid(True, linestyle=':')
plt.tight_layout()

plt.savefig('failure_rates_comparison_bw.png', dpi=300)
plt.show()
