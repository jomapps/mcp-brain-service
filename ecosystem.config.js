module.exports = {
  apps: [{
    name: 'mcp-brain-service',
    cwd: '/var/www/mcp-brain-service',
    script: 'venv/bin/python',
    args: '-m src.main',
    interpreter: 'none',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/var/log/mcp-brain-service-error.log',
    out_file: '/var/log/mcp-brain-service-out.log',
    log_file: '/var/log/mcp-brain-service-combined.log',
    time: true
  }]
};

