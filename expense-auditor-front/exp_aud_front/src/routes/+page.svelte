<script>
  import { uploadDocuments } from '$lib/api.js';

  let files = [];
  let isProcessing = false;
  let isDragging = false;
  
  // Mock data to simulate backend response from FastAPI/LangChain
  let expenses = [
    { id: 1, date: '2026-04-02', merchant: 'Office Depot', amount: 150.75, category: 'Supplies', status: 'Verified' },
    { id: 2, date: '2026-04-03', merchant: 'Delta Airlines', amount: 450.00, category: 'Travel', status: 'Pending' }
  ];

  function handleFileChange(event) {
    files = Array.from(event.target.files);
  }

  function handleDrop(event) {
    event.preventDefault();
    isDragging = false;
    if (event.dataTransfer?.files?.length > 0) {
      files = Array.from(event.dataTransfer.files);
    }
  }

  function handleDragOver(event) {
    event.preventDefault();
    isDragging = true;
  }

  async function uploadReceipts() {
    if (files.length === 0) return;
    
    isProcessing = true;
    
    try {
      const newExpenses = await uploadDocuments(files);
      expenses = [...newExpenses, ...expenses];
      files = [];
    } catch (error) {
      console.error("Error processing receipts:", error);
      alert(`Upload Failed:\n\n${error.message}\n\nPlease check your backend logs.`);
    } finally {
      isProcessing = false;
    }
  }
</script>

<svelte:head>
  <title>Dashboard | Expense Auditor</title>
</svelte:head>

<div class="dashboard">
  <section class="card upload-section">
    <h3>Upload Receipts & Invoices</h3>
    <p class="subtitle">Upload your documents for AI-powered OCR and auditing.</p>
    
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="file-drop-area" class:dragging={isDragging} on:drop={handleDrop} on:dragover={handleDragOver} on:dragleave={() => isDragging = false}>
      <input type="file" id="receipt-upload" multiple accept="image/*,.pdf" on:change={handleFileChange} />
      <label for="receipt-upload">
        {#if files.length > 0}
          <span class="file-count">{files.length} document(s) ready to process</span>
        {:else}
          <span>Drag & drop files here, or click to browse</span>
        {/if}
      </label>
    </div>
    
    <button class="btn-primary" disabled={files.length === 0 || isProcessing} on:click={uploadReceipts}>
      {isProcessing ? 'Processing with AI...' : 'Audit Receipts'}
    </button>
  </section>

  <section class="card expenses-section">
    <h3>Recent Audits</h3>
    <table class="data-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Merchant</th>
          <th>Category</th>
          <th>Amount</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {#each expenses as expense (expense.id)}
          <tr>
            <td>{expense.date}</td>
            <td><strong>{expense.merchant}</strong></td>
            <td><span class="badge gray">{expense.category}</span></td>
            <td>${expense.amount.toFixed(2)}</td>
            <td>
              <span class="badge status-{expense.status.toLowerCase()}">
                {expense.status}
              </span>
            </td>
            <td><button class="btn-secondary">Review</button></td>
          </tr>
        {/each}
        {#if expenses.length === 0}
          <tr>
            <td colspan="6" class="empty-state">No expenses found. Upload a receipt to begin.</td>
          </tr>
        {/if}
      </tbody>
    </table>
  </section>
</div>