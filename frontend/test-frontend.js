/**
 * Simple test script for frontend
 * Run with: node test-frontend.js
 */

const axios = require('axios')

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

async function testHealthCheck() {
  console.log('\n='.repeat(60))
  console.log('Testing Backend Connection')
  console.log('='.repeat(60))
  
  try {
    const response = await axios.get(API_URL.replace('/api', '/health'))
    console.log('✓ Backend is reachable')
    console.log(`  Status: ${response.data.status}`)
    console.log(`  GPU Available: ${response.data.gpu_available}`)
    return true
  } catch (error) {
    console.error('✗ Backend is not reachable')
    console.error(`  Error: ${error.message}`)
    return false
  }
}

async function testTextGeneration() {
  console.log('\n='.repeat(60))
  console.log('Testing Text Generation Endpoint')
  console.log('='.repeat(60))
  
  try {
    const response = await axios.post(`${API_URL}/generate/text`, {
      prompt: 'Hello from frontend test!',
      temperature: 0.7
    })
    console.log('✓ Text generation endpoint works')
    console.log(`  Request ID: ${response.data.request_id}`)
    console.log(`  Response: ${response.data.text.substring(0, 100)}...`)
    return true
  } catch (error) {
    console.error('✗ Text generation failed')
    console.error(`  Error: ${error.message}`)
    return false
  }
}

async function main() {
  console.log('\n╔═══════════════════════════════════════════════════════════╗')
  console.log('║            LUMEN Frontend Test Suite                     ║')
  console.log('╚═══════════════════════════════════════════════════════════╝')
  console.log(`\nTesting API at: ${API_URL}`)
  
  const healthOk = await testHealthCheck()
  
  if (healthOk) {
    await testTextGeneration()
  }
  
  console.log('\n='.repeat(60))
  console.log('Test Complete')
  console.log('='.repeat(60) + '\n')
}

main()
