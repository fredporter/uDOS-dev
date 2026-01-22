<script lang="ts">
  interface StatusItem {
    label: string;
    value: string;
  }

  let status: StatusItem[] = [
    { label: 'Version', value: '0.2.0' },
    { label: 'Status', value: 'Experimental' },
    { label: 'Port', value: '8767' },
    { label: 'Scope', value: 'Local Only' },
    { label: 'API Prefix', value: '/api/v0' },
    { label: 'Host', value: '127.0.0.1' },
  ];
</script>

<div class="status-banner">
  <span>⚠️ UNSTABLE API - EXPECT BREAKING CHANGES</span>
</div>

<div class="grid">
  {#each status as item (item.label)}
    <div class="item">
      <label>{item.label}</label>
      <div class="value">{item.value}</div>
    </div>
  {/each}
</div>

<style>
  .status-banner {
    display: inline-block;
    padding: 8px 16px;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 6px;
    color: #856404;
    margin-bottom: 30px;
    font-weight: 600;
    width: 100%;
    text-align: center;
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin: 30px 0;
  }

  .item {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    text-align: left;
  }

  label {
    font-weight: 600;
    color: #333;
    display: block;
    font-size: 0.85em;
    text-transform: uppercase;
    margin-bottom: 5px;
  }

  .value {
    color: #667eea;
    font-size: 1.1em;
    font-weight: 500;
  }
</style>
