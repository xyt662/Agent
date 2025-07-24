#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度地图API KEY验证脚本
"""

import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_baidu_api_key():
    """测试百度地图API KEY是否有效"""
    api_key = os.getenv('BAIDU_MAP_API_KEY')
    
    if not api_key:
        print("❌ 未找到BAIDU_MAP_API_KEY环境变量")
        return False
    
    print(f"🔑 使用API KEY: {api_key[:10]}...{api_key[-4:]}")
    
    # 测试地理编码API
    url = "https://api.map.baidu.com/geocoding/v3/"
    params = {
        'address': '上海市',
        'output': 'json',
        'ak': api_key
    }
    
    try:
        print("🌐 正在测试百度地图地理编码API...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📊 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 API响应: {data}")
            
            if data.get('status') == 0:
                print("✅ API KEY有效！地理编码测试成功")
                location = data.get('result', {}).get('location', {})
                print(f"📍 上海市坐标: 经度={location.get('lng')}, 纬度={location.get('lat')}")
                return True
            else:
                print(f"❌ API返回错误: status={data.get('status')}, message={data.get('message')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    print("🚀 百度地图API KEY验证测试")
    print("=" * 50)
    
    success = test_baidu_api_key()
    
    if success:
        print("\n🎉 测试通过！API KEY有效")
    else:
        print("\n💥 测试失败！请检查API KEY")
        print("\n💡 可能的解决方案:")
        print("1. 检查API KEY是否正确")
        print("2. 检查API KEY是否已过期")
        print("3. 检查API KEY的配额是否用完")
        print("4. 检查网络连接")