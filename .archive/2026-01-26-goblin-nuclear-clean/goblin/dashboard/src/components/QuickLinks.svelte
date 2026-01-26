<script lang="ts">
  interface Link {
    href: string;
    label: string;
    icon: string;
    className: string;
  }

  let links: Link[] = [
    {
      href: '/docs',
      label: 'API Docs (Swagger)',
      icon: '📚',
      className: 'btn-docs',
    },
    {
      href: '/api/v0/info',
      label: 'Server Info (JSON)',
      icon: '📋',
      className: 'btn-info',
    },
  ];
</script>

<div class="links">
  {#each links as link (link.href)}
    <a href={link.href} class={link.className}>
      {link.icon} {link.label}
    </a>
  {/each}
</div>

<style>
  .links {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin: 30px 0;
  }

  a {
    display: block;
    padding: 15px;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
    text-align: center;
  }

  .btn-docs {
    background: #667eea;
    color: white;
  }

  .btn-docs:hover {
    background: #5568d3;
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
  }

  .btn-info {
    background: #e9ecef;
    color: #333;
  }

  .btn-info:hover {
    background: #dee2e6;
    transform: translateY(-2px);
  }
</style>
