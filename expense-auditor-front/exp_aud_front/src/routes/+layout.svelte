<script>
  import '../app.css';
</script>

<div class="app-layout">
  <header class="navbar">
    <div class="logo">
      <h2>📊 Expense Auditor</h2>
    </div>
    <nav>
      <ul>
        <li><a href="/">Dashboard</a></li>
        <li><a href="#">Reports</a></li>
        <li><a href="#">Settings</a></li>
      </ul>
    </nav>
  </header>

  <main class="content">
    <slot />
  </main>
</div>