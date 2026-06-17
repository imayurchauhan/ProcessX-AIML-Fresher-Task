import { existsSync } from 'node:fs'
import { spawn, spawnSync } from 'node:child_process'
import { join } from 'node:path'
import process from 'node:process'

const root = process.cwd()
const venvDir = join(root, '.venv')
const venvPython = join(venvDir, 'Scripts', 'python.exe')

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: 'inherit', shell: false, ...options })
  if (result.status !== 0) {
    process.exit(result.status ?? 1)
  }
}

if (!existsSync(venvPython)) {
  run('py', ['-3.13', '-m', 'venv', '.venv'])
}

run(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip'])
run(venvPython, ['-m', 'pip', 'install', '-r', 'requirements.txt'])

const backend = spawn(venvPython, ['-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload'], {
  stdio: 'inherit',
  shell: false
})

const frontend = spawn('npx', ['vite', '--config', 'vite.config.ts'], {
  stdio: 'inherit',
  shell: true
})

const shutdown = () => {
  if (!backend.killed) backend.kill()
  if (!frontend.killed) frontend.kill()
}

process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)

Promise.all([
  new Promise((_, reject) => backend.on('exit', code => code === 0 ? reject(new Error('backend exited')) : reject(new Error(`backend exited with ${code}`)))),
  new Promise((_, reject) => frontend.on('exit', code => code === 0 ? reject(new Error('frontend exited')) : reject(new Error(`frontend exited with ${code}`))))
]).catch(() => shutdown())