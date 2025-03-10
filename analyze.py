import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Button

# 各点の名前（Azure Kinectの定義）
joint_names = [
    "PELVIS", "SPINE_NAVAL", "SPINE_CHEST", "NECK", 
    "CLAVICLE_LEFT", "SHOULDER_LEFT", "ELBOW_LEFT", "WRIST_LEFT", "HAND_LEFT", "HANDTIP_LEFT", "THUMB_LEFT", 
    "CLAVICLE_RIGHT", "SHOULDER_RIGHT", "ELBOW_RIGHT", "WRIST_RIGHT", "HAND_RIGHT", "HANDTIP_RIGHT", "THUMB_RIGHT", 
    "HIP_LEFT", "KNEE_LEFT", "ANKLE_LEFT", "FOOT_LEFT", 
    "HIP_RIGHT", "KNEE_RIGHT", "ANKLE_RIGHT", "FOOT_RIGHT", 
    "HEAD", "NOSE", "EYE_LEFT", "EAR_LEFT", "EYE_RIGHT", "EAR_RIGHT"
]

# 各点に対応する色
joint_colors = {
    "PELVIS": "navy", "SPINE_NAVAL": "blue", "SPINE_CHEST": "dodgerblue", "NECK": "deepskyblue", 
    "CLAVICLE_LEFT": "limegreen", "SHOULDER_LEFT": "forestgreen", "ELBOW_LEFT": "mediumseagreen", 
    "WRIST_LEFT": "seagreen", "HAND_LEFT": "green", "HANDTIP_LEFT": "darkgreen", "THUMB_LEFT": "lightgreen", 
    "CLAVICLE_RIGHT": "hotpink", "SHOULDER_RIGHT": "red", "ELBOW_RIGHT": "orangered", 
    "WRIST_RIGHT": "firebrick", "HAND_RIGHT": "darkred", "HANDTIP_RIGHT": "crimson", "THUMB_RIGHT": "salmon", 
    "HIP_LEFT": "orange", "KNEE_LEFT": "darkorange", "ANKLE_LEFT": "chocolate", "FOOT_LEFT": "saddlebrown", 
    "HIP_RIGHT": "purple", "KNEE_RIGHT": "mediumpurple", "ANKLE_RIGHT": "darkviolet", "FOOT_RIGHT": "indigo", 
    "HEAD": "gold", "NOSE": "yellow", "EYE_LEFT": "khaki", "EAR_LEFT": "goldenrod", 
    "EYE_RIGHT": "khaki", "EAR_RIGHT": "goldenrod"
}

# 点の数（Azure Kinect の定義）
joint_count = len(joint_names)

def load_data(date_folder):
    """ 指定した日付フォルダ内のすべてのCSVファイルを取得し、ラベルごとに整理 """
    base_path = os.path.join("temp", date_folder)
    data = {}

    if not os.path.exists(base_path):
        print(f"指定されたフォルダ '{base_path}' が見つかりません。")
        return data

    for time_folder in os.listdir(base_path):
        file_path = os.path.join(base_path, time_folder, "0", "pos.csv")

        if os.path.exists(file_path):
            df = pd.read_csv(file_path, header=None)
            if df.empty:
                print(f"警告: {file_path} が空です。スキップします。")
                continue

            label = df.iloc[0, 0]  # 各CSVのラベル番号
            data.setdefault(label, []).append(df)

    return data

def compute_joint_statistics(df_list):
    """ 各関節ごとの座標の標準偏差を計算 """
    std_values = []

    for i in range(joint_count):
        xyz = np.array([df.iloc[:, 2 + i*3:5 + i*3].dropna().values for df in df_list])
        if xyz.size == 0:
            continue
        
        xyz_flat = xyz.reshape(-1, 3)
        
        # 関節の座標データから指標を計算
        std_xyz = np.nanstd(xyz_flat, axis=0)
        std_values.append(np.mean(std_xyz))

    # 3軸の標準偏差の平均を各点分集め、それらの平均をそのラベル全体のばらつきの指標とする
    return np.nanmean(std_values)

def compute_statistics(data):
    """ 各ラベルごとに統計情報を算出 """
    stats = {}

    for label, df_list in data.items():
        mean_std = compute_joint_statistics(df_list)
        stats[label] = {
            "mean_std": mean_std
        }

    return stats

def plot_statistics(ax, stats):
    """ ラベルごとの統計情報を棒グラフで表示 """
    labels = list(stats.keys())
    mean_std = [stats[label]["mean_std"] for label in labels]

    x_positions = np.arange(len(labels))

    ax.bar(x_positions, mean_std, 0.4, color="royalblue")

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)

    ax.set_title("Mean Standard Deviation for each labels")

def plot_3d_scatter(ax, data, current_label):
    """ 3D散布図を表示 """
    ax.clear()  # プロットをクリア

    df_list = data[current_label]
    for df in df_list:
        for i in range(joint_count):
            joint_name = joint_names[i]
            # Azure Kinect の座標系に合わせて変換する
            new_x = df.iloc[:, 4 + i * 3] # 元 z座標
            new_y = df.iloc[:, 3 + i * 3] # 元 y座標
            new_z = -1 * df.iloc[:, 2 + i * 3] # 元 x座標

            ax.scatter(new_x, new_y, new_z, label=joint_name, color=joint_colors[joint_name], alpha=0.7)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(f"3D Scatter Plot (Label: {current_label})")
    ax.legend(bbox_to_anchor=(0.05, 1), loc="upper right", fontsize=7)

def update_plot(event, data, ax2, current_label_text):
    """ ボタンが押されたときにプロットを更新 """
    current_label = int(current_label_text[0])
    label_list = list(data.keys())
    
    # ラベル番号の更新
    next_label = label_list[(label_list.index(current_label) + 1) % len(label_list)]
    current_label_text[0] = str(next_label)  # 次のラベル番号を保存
    
    # 散布図を更新
    plot_3d_scatter(ax2, data, next_label)
    plt.draw()

# メイン処理
date_folder = input("日付フォルダ名を入力してください（例: 20250303）: ")
data = load_data(date_folder)
if not data:
    print("データが見つかりませんでした。")
else:
    stats = compute_statistics(data)

    # サブプロットの作成（1行2列）
    fig = plt.figure(figsize=(14, 7))

    # 左側に統計グラフ
    ax1 = fig.add_subplot(121)
    plot_statistics(ax1, stats)

    # 右側に3D散布図
    ax2 = fig.add_subplot(122, projection='3d')
    current_label = list(data.keys())[0]  # 最初のラベルを初期選択
    plot_3d_scatter(ax2, data, current_label)

    # ボタンの作成
    ax_button = fig.add_axes([0.93, 0.03, 0.05, 0.055])
    button = Button(ax_button, "Next")
    current_label_text = [str(current_label)]  # 現在のラベルを格納
    button.on_clicked(lambda event: update_plot(event, data, ax2, current_label_text))

    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.4)
    plt.show()