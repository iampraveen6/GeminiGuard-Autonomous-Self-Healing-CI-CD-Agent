# ==========================================
# STAGE 1: Builder (Install dependencies)
# ==========================================
FROM python:3.10-slim AS builder

WORKDIR /app

# Upgrade pip bypassing corporate SSL interception
RUN pip install --no-cache-dir --upgrade pip \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.python.org

# Copy and install Python requirements bypassing corporate SSL interception
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.python.org

# ==========================================
# STAGE 2: Runner (Final lightweight image)
# ==========================================
FROM python:3.10-slim AS runner

WORKDIR /app

# Copy the installed python packages from the builder stage
COPY --from=builder /root/.local /root/.local

# 🔥 FIX: Copy everything (including agents/, dashboard/, etc.)
COPY . .

# Update PATH so the system can find the installed streamlit binary and libs
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV TEST_MODE=false

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]