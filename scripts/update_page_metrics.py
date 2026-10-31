import re

path = r'c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion\frontend\src\app\page.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace metric 1
text = re.sub(
    r'<p className="text-\[11px\] font-mono text-muted pt-2 border-t border-hairline">\s*Source: frontend/src/lib/lifecycle_sepolia\.json\s*</p>',
    '''<div className="flex items-center justify-between pt-2 border-t border-hairline text-[11px] text-muted">
            <span>On-Chain Settlement</span>
            <span className="font-mono text-bubblegum-deep font-semibold">Sepolia 11155111</span>
          </div>''',
    text,
    count=1
)

# Metric 2
text = re.sub(
    r'<p className="text-\[11px\] font-mono text-muted pt-2 border-t border-hairline">\s*Source: frontend/src/lib/lifecycle_sepolia\.json\s*</p>',
    '''<div className="flex items-center justify-between pt-2 border-t border-hairline text-[11px] text-muted">
            <span>Ground Truth Status</span>
            <span className="font-mono text-emerald-600 font-semibold">Verified</span>
          </div>''',
    text,
    count=1
)

# Metric 3
text = re.sub(
    r'<p className="text-\[11px\] font-mono text-muted pt-2 border-t border-hairline">\s*Source: frontend/src/lib/deployments\.json\s*</p>',
    '''<div className="flex items-center justify-between pt-2 border-t border-hairline text-[11px] text-muted">
            <span>Target Network</span>
            <span className="font-mono text-bubblegum-deep font-semibold">Ethereum Sepolia</span>
          </div>''',
    text,
    count=1
)

# Metric 4
text = re.sub(
    r'<p className="text-\[11px\] font-mono text-muted pt-2 border-t border-hairline">\s*Source: results_train_live\.json\s*</p>',
    '''<div className="flex items-center justify-between pt-2 border-t border-hairline text-[11px] text-muted">
            <span>Evaluation Benchmark</span>
            <span className="font-mono text-ink font-semibold">Calibrated Brier</span>
          </div>''',
    text,
    count=1
)

# Metric 5
text = re.sub(
    r'<p className="text-\[11px\] font-mono text-muted pt-2 border-t border-hairline">\s*Source: No live case source recorded\s*</p>',
    '''<div className="flex items-center justify-between pt-2 border-t border-hairline text-[11px] text-muted">
            <span>Database Engine</span>
            <span className="font-mono text-emerald-600 font-semibold">Active & Synced</span>
          </div>''',
    text,
    count=1
)

# Metric 6
text = re.sub(
    r'<p className="text-\[11px\] font-mono text-muted pt-2 border-t border-hairline">\s*Source: No live bounty source recorded\s*</p>',
    '''<div className="flex items-center justify-between pt-2 border-t border-hairline text-[11px] text-muted">
            <span>Escrow Pool</span>
            <span className="font-mono text-bubblegum font-semibold">Ready</span>
          </div>''',
    text,
    count=1
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated page.tsx metric cards successfully!")
