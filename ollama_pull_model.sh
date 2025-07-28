#!/bin/bash

ollama serve &

echo "Waiting for Ollama server to be active..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done
echo "Ollama server is active."

echo "Pulling qwen3:4b model..."
ollama pull qwen3:4b

wait $!