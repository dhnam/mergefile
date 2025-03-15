import tkinter as tk
from tkinter import filedialog
from pathlib import Path

class DirectorySelector(tk.Toplevel):
    def __init__(self, master=None, title="Select Directories", initialdir=None):
        super().__init__(master)
        self.title(title)
        self.initialdir = initialdir or Path.home()

        self.selected_directories = []
        self.selected_parent_dir = None  # 선택된 부모 디렉토리 저장

        # 항상 최상위로 표시하도록 설정
        self.attributes("-topmost", 1)

        # UI 요소 설정
        self.parent_dir_button = tk.Button(self, text="Select Parent Directory", command=self.select_parent_directory)
        self.parent_dir_button.pack(pady=10)

        # 부모 디렉터리 이름을 보여줄 라벨 추가
        self.parent_dir_label = tk.Label(self, text="No parent directory selected", anchor="w")
        self.parent_dir_label.pack(fill="both", padx=10)

        # Listbox와 Scrollbar 설정 (Listbox와 Scrollbar를 Frame 내부에 배치)
        self.listbox_frame = tk.Frame(self)
        self.listbox_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical")
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

        self.listbox = tk.Listbox(self.listbox_frame, selectmode=tk.EXTENDED, height=10, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill="both", expand=True)

        # 스크롤바와 Listbox 연결
        self.scrollbar.config(command=self.listbox.yview)

        self.confirm_button = tk.Button(self, text="Confirm", command=self.confirm_selection)
        self.confirm_button.pack(side=tk.RIGHT, padx=5, pady=10)

        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel_selection)
        self.cancel_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.geometry("400x300")

    def select_parent_directory(self):
        """부모 디렉토리를 선택하고, 그 하위 디렉토리들을 Listbox에 추가"""
        selected_dir = filedialog.askdirectory(initialdir=self.initialdir)
        if selected_dir:
            self.selected_parent_dir = Path(selected_dir)  # 선택된 부모 디렉토리 저장
            self.initialdir = self.selected_parent_dir  # 이후 경로는 선택한 디렉토리로 설정
            self.parent_dir_label.config(text=f"Parent Directory: {self.selected_parent_dir.name}")  # 부모 디렉터리 이름 표시
            self.listbox.delete(0, tk.END)  # 이전 목록을 지우고
            self.add_subdirectories(self.selected_parent_dir)  # 선택한 부모 디렉토리로 하위 디렉토리 목록 갱신

    def add_subdirectories(self, parent_dir):
        """선택한 부모 디렉토리의 하위 디렉토리들을 Listbox에 추가 (이름만 표시)"""
        try:
            subdirectories = [d for d in parent_dir.iterdir() if d.is_dir()]
            for subdir in subdirectories:
                self.listbox.insert(tk.END, subdir.name)  # 디렉토리 이름만 Listbox에 추가
        except Exception as e:
            print(f"Error adding subdirectories: {e}")

    def confirm_selection(self):
        """확인 버튼 클릭 시, 선택된 디렉토리들을 반환"""
        if self.selected_parent_dir:
            selected_indices = self.listbox.curselection()
            self.selected_directories = [self.selected_parent_dir / self.listbox.get(i) for i in selected_indices]  # 선택된 하위 디렉토리 경로 저장
            self.destroy()

    def cancel_selection(self):
        """취소 버튼 클릭 시 빈 리스트 반환"""
        self.selected_directories = []
        self.destroy()


def ask_multi_directory(title: str = "Select Directories", initialdir: Path | None = None) -> list[Path]:
    root = tk.Tk()
    root.withdraw()  # 기본 루트 창 숨기기

    dialog = DirectorySelector(master=root, title=title, initialdir=initialdir)
    root.wait_window(dialog)  # 다이얼로그가 닫힐 때까지 기다기

    return dialog.selected_directories


def main():
    directories = ask_multi_directory()
    if not directories:
        print("디렉토리 선택이 취소되었습니다.")
    else:
        for directory in directories:
            print(f"선택된 디렉토리: {directory}")

if __name__ == "__main__":
    main()
