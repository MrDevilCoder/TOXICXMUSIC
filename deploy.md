# Deployment Guide

## Option 1: Deploy on Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   
3. **Configure Service**
   - Name: `telegram-music-bot`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Plan: Free

4. **Environment Variables**
