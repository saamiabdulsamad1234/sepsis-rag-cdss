#!/bin/bash

echo "========================================"
echo "Sepsis RAG v2.0 - Startup Script"
echo "========================================"
echo ""

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo " Python 3 not found. Please install Python 3.9+"
        exit 1
    fi
    echo " Python 3 found: $(python3 --version)"
}

check_env() {
    if [ ! -f ".env" ]; then
        echo "  .env file not found. Creating from template..."
        cp .env.template .env
        echo " Please edit .env and add your API keys"
        exit 1
    fi
    echo " .env file exists"
}

install_deps() {
    echo ""
    echo " Installing dependencies..."
    pip install -r requirements.txt --quiet
    if [ $? -eq 0 ]; then
        echo " Dependencies installed"
    else
        echo " Failed to install dependencies"
        exit 1
    fi
}

index_docs() {
    echo ""
    echo " Indexing clinical guidelines..."
    python3 scripts/index_documents.py
    if [ $? -eq 0 ]; then
        echo " Documents indexed successfully"
    else
        echo " Failed to index documents"
        exit 1
    fi
}

create_test_patients() {
    echo ""
    echo " Creating test patients..."
    python3 scripts/create_test_patients.py
    if [ $? -eq 0 ]; then
        echo " Test patients created"
    else
        echo "  Failed to create test patients (non-critical)"
    fi
}

start_backend() {
    echo ""
    echo " Starting backend server..."
    cd backend
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    cd ..
    sleep 3
    
    if curl -s http://localhost:8000/health > /dev/null; then
        echo " Backend running at http://localhost:8000"
    else
        echo " Backend failed to start"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
}

start_frontend() {
    echo ""
    echo " Starting frontend..."
    streamlit run frontend/app.py --server.port 8501 &
    FRONTEND_PID=$!
    sleep 3
    echo " Frontend running at http://localhost:8501"
}

cleanup() {
    echo ""
    echo " Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo " Shutdown complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

main() {
    check_python
    check_env
    
    echo ""
    read -p "Install/update dependencies? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_deps
    fi
    
    echo ""
    read -p "Re-index documents? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        index_docs
    fi
    
    echo ""
    read -p "Create test patients? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_test_patients
    fi
    
    start_backend
    start_frontend
    
    echo ""
    echo "========================================"
    echo " System Ready!"
    echo "========================================"
    echo ""
    echo " Backend API: http://localhost:8000"
    echo " Frontend UI: http://localhost:8501"
    echo " API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo ""
    
    wait
}

main
