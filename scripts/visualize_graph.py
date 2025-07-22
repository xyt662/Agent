# 文件: scripts/visualize_graph.py

import sys
from pathlib import Path

# --- 路径设置 ---
# 这部分和你 run.py 的逻辑一样，确保能找到 src 目录
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# --- 导入必要的模块 ---
from rag_agent.factories.agent_factory import get_main_agent_runnable

def main():
    """
    一个专门用于生成并保存 Agent 图可视化图片的脚本。
    """
    print("🚀 开始生成 Agent 图的可视化图片...")

    try:
        # 1. 获取已编译的 Agent 应用实例
        # get_main_agent_runnable() 内部会处理所有组件的组装和编译
        app = get_main_agent_runnable()
        print("   ✅ Agent 应用实例加载成功。")

        # 2. 从已编译的应用中获取图的图形表示
        # .get_graph() 是 LangGraph 的内置方法
        graph = app.get_graph()
        print("   ✅ 图形结构获取成功。")

        # 3. 生成并保存图片
        # 调用 .draw_mermaid_png() 方法生成 PNG 图片
        output_path = project_root / "agent_graph.png"
        png_data = graph.draw_mermaid_png()
        
        # 将图片数据写入文件
        with open(output_path, "wb") as f:
            f.write(png_data)
        
        print(f"\n🎉 成功生成 Agent 图！")
        print(f"   图片已保存至: {output_path}")

    except ImportError as e:
        if "pygraphviz" in str(e):
            print("\n❌ 错误：缺少 pygraphviz 库。")
            print("   请按照以下步骤安装所需依赖：")
            print("   1. 安装系统级 Graphviz 软件 (例如在 macOS 上: `brew install graphviz`)")
            print("   2. 安装 Python 包: `pip install pygraphviz`")
        else:
            print(f"❌ 发生导入错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 生成图片时发生未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()