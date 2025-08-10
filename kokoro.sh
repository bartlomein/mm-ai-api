#!/bin/bash

# Script to manage Kokoro TTS container

case "$1" in
    start)
        echo "Starting Kokoro TTS container..."
        docker-compose up -d kokoro
        echo "Waiting for Kokoro to be ready..."
        sleep 5
        
        # Check if Kokoro is running
        if curl -f http://localhost:8880/health > /dev/null 2>&1; then
            echo "✅ Kokoro TTS is running at http://localhost:8880"
            echo "Available endpoints:"
            echo "  - POST http://localhost:8880/v1/audio/speech"
            echo "  - GET  http://localhost:8880/health"
            echo "  - GET  http://localhost:8880/voices"
        else
            echo "⚠️ Kokoro might still be starting up. Check logs with: docker-compose logs kokoro"
        fi
        ;;
        
    stop)
        echo "Stopping Kokoro TTS container..."
        docker-compose stop kokoro
        ;;
        
    restart)
        echo "Restarting Kokoro TTS container..."
        docker-compose restart kokoro
        ;;
        
    logs)
        docker-compose logs -f kokoro
        ;;
        
    test)
        echo "Testing Kokoro TTS..."
        curl -X POST http://localhost:8880/v1/audio/speech \
            -H "Content-Type: application/json" \
            -d '{
                "model": "kokoro",
                "input": "Hello! This is a test of the Kokoro text to speech system.",
                "voice": "af_bella",
                "response_format": "mp3"
            }' \
            -o test_kokoro.mp3
        
        if [ -f test_kokoro.mp3 ]; then
            echo "✅ Test audio saved to test_kokoro.mp3"
            echo "File size: $(ls -lh test_kokoro.mp3 | awk '{print $5}')"
        else
            echo "❌ Test failed"
        fi
        ;;
        
    voices)
        echo "Fetching available voices..."
        curl -s http://localhost:8880/voices | python3 -m json.tool
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|logs|test|voices}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Kokoro TTS container"
        echo "  stop    - Stop the Kokoro TTS container"
        echo "  restart - Restart the Kokoro TTS container"
        echo "  logs    - Show container logs"
        echo "  test    - Generate a test audio file"
        echo "  voices  - List available voices"
        exit 1
        ;;
esac