import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import multi_selector  # 우리가 만든 multi_selector 모듈
from datetime import datetime
import random
import glob  # glob 모듈 추가
from collections import defaultdict

class FileNameTemplate:
    def __init__(self, template: str, original_name: str):
        self.template = template
        self.original_name = original_name
        self.original_name_without_ext, self.original_ext = os.path.splitext(original_name)

    def generate(self, count: int = 1):
        """
        주어진 count 값에 맞춰 <NUM>을 변경한 새로운 이름을 반환합니다.
        :param count: <NUM>에 들어갈 숫자 값
        :return: 변경된 이름
        """
        name = self.template
        name = self._apply_number(name, count)
        name = self._apply_date(name)
        name = self._apply_time(name)
        name = self._apply_random(name)
        name = self._apply_original(name)

        # 확장자가 있다면 무조건 마지막에 붙도록 처리
        if self.original_ext:
            name += self.original_ext

        return name

    def _apply_number(self, name: str, num: int):
        return name.replace("<NUM>", str(num))

    def _apply_date(self, name: str):
        if "<DATE>" in name:
            date_str = datetime.now().strftime("%Y%m%d")
            name = name.replace("<DATE>", date_str)
        return name

    def _apply_time(self, name: str):
        if "<TIME>" in name:
            time_str = datetime.now().strftime("%H%M%S")
            name = name.replace("<TIME>", time_str)
        return name

    def _apply_random(self, name: str):
        if "<RAND>" in name:
            rand_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
            name = name.replace("<RAND>", rand_str)
        return name

    def _apply_original(self, name: str):
        if "<ORIGINAL>" in name:
            name = name.replace("<ORIGINAL>", self.original_name_without_ext)
        return name


def apply_template(directories: list[Path], template: str, apply_template_to_non_duplicate: bool, file_pattern: str):
    all_files = set()  # 전체 파일명을 저장하는 집합
    name_counts = defaultdict(int)  # 파일 등장 횟수
    duplicate_files = set()  # 중복된 파일을 저장하는 집합
    sorted_directories = sorted(directories)  # 정렬된 디렉터리 리스트
    file_name_templates = {}  # 원본 파일 -> 새 파일명 매핑

    # 1. 모든 파일을 가져오고 중복된 파일을 찾기
    files_by_parent = defaultdict(list)
    for directory in sorted_directories:
        files = glob.glob(str(directory / file_pattern))
        for file_path in files:
            file = Path(file_path)
            files_by_parent[directory].append(file)
            full_name = file.name
            name_counts[full_name] += 1
            if name_counts[full_name] > 1:
                duplicate_files.add(full_name)

    # 2. 템플릿 수정 (필요한 경우 "_<NUM>" 추가)
    if "<NUM>" not in template and "<RAND>" not in template:
        template += "_<NUM>"

    # 3. 각 파일에 대해 템플릿 적용
    global_counter = defaultdict(int)  # 파일별 글로벌 카운터 (중복 발생 시 사용)
    for directory in sorted_directories:
        for file in files_by_parent[directory]:
            full_name = file.name
            if not apply_template_to_non_duplicate and full_name not in duplicate_files:
                # 중복되지 않은 파일이고, apply_template_to_non_duplicate가 False이면 원래 이름 유지
                new_name = full_name
            else:
                count = global_counter[full_name] + 1
                global_counter[full_name] = count

                filename_generator = FileNameTemplate(template, full_name)
                new_name = filename_generator.generate(count)

                # 중복 방지를 위해 이름이 이미 존재하면 숫자를 증가시키면서 반복
                while new_name in all_files:
                    count += 1
                    global_counter[full_name] = count
                    new_name = filename_generator.generate(count)

            all_files.add(new_name)
            file_name_templates[file] = new_name

    return file_name_templates


def update_preview(source_directories, template, apply_template_to_non_duplicate, file_pattern, listbox_orig, listbox_new):
    # 소스 디렉토리만 선택된 경우에도 미리보기는 정상적으로 업데이트되도록 수정
    if not source_directories:
        return

    listbox_orig.delete(0, tk.END)
    listbox_new.delete(0, tk.END)

    # 타겟 디렉토리가 선택되지 않더라도 미리보기만 업데이트
    file_name_templates = apply_template(source_directories, template, apply_template_to_non_duplicate, file_pattern)

    for original_file, new_name in file_name_templates.items():
        listbox_orig.insert(tk.END, f"{original_file.parent.name}/{original_file.name}")
        listbox_new.insert(tk.END, new_name)




def copy_files_to_target(directories: list[Path], target_dir: Path, template: str, apply_template_to_non_duplicate: bool, file_pattern: str):
    # 타겟 디렉토리가 반드시 선택되어야 복사가 진행되도록 수정
    if not target_dir:
        messagebox.showwarning("경고", "대상 디렉토리를 선택하지 않았습니다.")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    file_name_templates = apply_template(directories, template, apply_template_to_non_duplicate, file_pattern)

    for file, new_name in file_name_templates.items():
        target_file = target_dir / new_name
        shutil.copy(file, target_file)
        print(f"파일 복사됨: {file} -> {target_file}")

    messagebox.showinfo("완료", "파일 복사가 완료되었습니다.")

class FileRenameApp:
    def __init__(self, root: tk.Tk):
        self.root: tk.Tk = root
        self.root.title("파일 이름 변경 및 합치기")

        # 변수 선언
        self.source_directories = []
        self.target_directory = None

        # UI 구성
        self.create_widgets()

    def create_widgets(self):
        """UI 요소를 생성하고 배치"""
        self.create_layout_frames()
        self.create_source_target_widgets()
        self.create_template_widgets()
        self.create_listbox_widgets()
        self.create_control_buttons()
        self.bind_events()

    def create_layout_frames(self):
        """레이아웃 프레임을 설정"""
        # 레이아웃 프레임
        self.top_frame = tk.Frame(self.root)
        self.top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.grid(row=1, column=0, sticky="ew", pady=10)

        # left_frame의 위젯들을 첫 번째 열에 배치
        self.create_source_target_widgets()
        self.create_template_widgets()

        # right_frame 내에서 Listbox들을 배치
        self.create_listbox_widgets()

    def create_source_target_widgets(self):
        """소스 및 대상 디렉토리 라벨과 버튼을 설정"""
        # 소스 및 대상 디렉토리 라벨
        self.source_label = tk.Label(self.top_frame, text="소스 디렉토리: 선택되지 않음", wraplength=400)
        self.source_label.grid(row=0, column=0, pady=5, sticky="ew")

        self.btn_select_source = tk.Button(self.top_frame, text="소스 디렉토리 선택", command=self.on_select_source)
        self.btn_select_source.grid(row=1, column=0, pady=10, sticky="ew")

        self.target_label = tk.Label(self.top_frame, text="대상 디렉토리: 선택되지 않음", wraplength=400)
        self.target_label.grid(row=2, column=0, pady=5, sticky="ew")

        self.btn_select_target = tk.Button(self.top_frame, text="대상 디렉토리 선택", command=self.on_select_target)
        self.btn_select_target.grid(row=3, column=0, pady=10, sticky="ew")

    def create_template_widgets(self):
        """파일 이름 템플릿 및 와일드카드 입력 필드를 설정"""
        tk.Label(self.top_frame, text="파일 이름 템플릿:").grid(row=4, column=0, pady=5, sticky="ew")
        self.template_entry = tk.Entry(self.top_frame, width=50)
        self.template_entry.insert(0, "<ORIGINAL>_<NUM>_<DATE>_<TIME>_<RAND>")
        self.template_entry.grid(row=5, column=0, pady=5, sticky="ew")

        tk.Label(self.top_frame, text="파일 선택 와일드카드 패턴 (예: *.txt):").grid(row=6, column=0, pady=5, sticky="ew")
        self.pattern_entry = tk.Entry(self.top_frame, width=50)
        self.pattern_entry.insert(0, "*.*")
        self.pattern_entry.grid(row=7, column=0, pady=5, sticky="ew")

        # 템플릿 적용 옵션
        self.apply_template_var = tk.IntVar(value=1)
        tk.Radiobutton(self.top_frame, text="중복된 파일에만 템플릿 적용", variable=self.apply_template_var, value=0).grid(row=8, column=0, pady=5, sticky="ew")
        tk.Radiobutton(self.top_frame, text="모든 파일에 템플릿 적용", variable=self.apply_template_var, value=1).grid(row=9, column=0, pady=5, sticky="ew")

    def create_listbox_widgets(self):
        """미리보기 Listbox 및 스크롤바를 설정"""
        # Listbox와 스크롤바를 top_frame의 1, 2, 3번 열에 배치
        self.listbox_orig = tk.Listbox(self.top_frame, width=50, selectmode=tk.SINGLE)
        self.listbox_orig.grid(row=0, column=1, padx=5, pady=10, sticky="ns", rowspan=10)  # rowspan으로 세로로 확장

        self.listbox_new = tk.Listbox(self.top_frame, width=50, selectmode=tk.SINGLE)
        self.listbox_new.grid(row=0, column=2, padx=0, pady=10, sticky="ns", rowspan=10)  # rowspan으로 세로로 확장

        # 스크롤바 추가
        scrollbar = tk.Scrollbar(self.top_frame, orient="vertical")
        scrollbar.grid(row=0, column=3, padx=0, pady=10, sticky="ns", rowspan=10)  # rowspan으로 세로로 확장

        # 스크롤 동기화
        scrollbar.config(command=self.sync_scroll)
        self.listbox_orig.config(yscrollcommand=scrollbar.set)
        self.listbox_new.config(yscrollcommand=scrollbar.set)

    def sync_scroll(self, *args):
        """리스트박스 스크롤 동기화"""
        self.listbox_orig.yview(*args)
        self.listbox_new.yview(*args)

    def create_control_buttons(self):
        """실행 버튼을 설정"""
        btn_start = tk.Button(self.bottom_frame, width=20, text="파일 합치기 시작", command=self.on_start_copy)
        btn_start.grid(row=0, column=0, pady=20, columnspan=2)

        # 중앙 정렬을 위한 grid 설정
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)


    def on_mouse_wheel(self, event):
        """마우스 휠 이벤트 처리"""
        delta = -1 * (event.delta // 120)  # Windows/Mac에서는 120 단위로 동작
        self.listbox_orig.yview_scroll(delta, "units")
        self.listbox_new.yview_scroll(delta, "units")
        return "break"

    def on_arrow_key(self, event):
        """방향키 이벤트 처리"""
        widget = event.widget  # 현재 키 입력이 발생한 위젯 (listbox_orig or listbox_new)

        if widget not in [self.listbox_orig, self.listbox_new]:
            return  # 리스트박스가 아닐 경우 무시

        selection = widget.curselection()

        if selection:
            current_index = selection[0]
        else:
            current_index = 0

        # 새로운 인덱스 계산
        if event.keysym == "Up":
            new_index = max(0, current_index - 1)
        elif event.keysym == "Down":
            new_index = min(widget.size() - 1, current_index + 1)
        else:
            return "break"

        # 선택된 항목을 해당 Listbox에만 반영
        widget.selection_clear(0, tk.END)  # 기존 선택 항목 해제
        widget.selection_set(new_index)  # 새로운 항목 선택

        # 선택된 항목을 화면에 보이게끔 스크롤
        widget.see(new_index)

        # 동기화: 현재 리스트박스에 선택된 항목만 반영하고, 다른 리스트박스는 손대지 않음
        if widget == self.listbox_orig:
            self.listbox_new.selection_clear(0, tk.END)  # 다른 Listbox는 선택 해제
            self.listbox_new.see(new_index)  # 스크롤 동기화
        elif widget == self.listbox_new:
            self.listbox_orig.selection_clear(0, tk.END)  # 다른 Listbox는 선택 해제
            self.listbox_orig.see(new_index)  # 스크롤 동기화

        return "break"

    def bind_events(self):
        """이벤트 핸들러를 바인딩"""
        # 이벤트 핸들러 연결
        self.template_entry.bind("<KeyRelease>", lambda e: self.update_preview())
        self.pattern_entry.bind("<KeyRelease>", lambda e: self.update_preview())
        self.apply_template_var.trace_add("write", lambda *args: self.update_preview())

        # 키보드 및 마우스 이벤트 바인딩
        self.listbox_orig.bind("<MouseWheel>", self.on_mouse_wheel)
        self.listbox_new.bind("<MouseWheel>", self.on_mouse_wheel)
        self.listbox_orig.bind("<Up>", self.on_arrow_key)
        self.listbox_orig.bind("<Down>", self.on_arrow_key)
        self.listbox_new.bind("<Up>", self.on_arrow_key)
        self.listbox_new.bind("<Down>", self.on_arrow_key)

        # 창 종료 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)



    def on_select_source(self):
        """소스 디렉토리 선택"""
        self.source_directories = multi_selector.ask_multi_directory(title="소스 디렉토리 선택")

        if not self.source_directories:
            messagebox.showwarning("경고", "소스 디렉토리를 선택하지 않았습니다.")
            return

        # 디렉토리의 마지막 요소(폴더명)만 추출
        directory_names = [directory.name for directory in self.source_directories]

        # 3개 이상이면 "dir1, dir2 ... (총 n개)" 형식으로 축약
        if len(directory_names) > 2:
            display_text = f"{directory_names[0]}, {directory_names[1]} ... (총 {len(directory_names)}개)"
        else:
            display_text = ", ".join(directory_names)

        self.source_label.config(text=f"소스 디렉토리: {display_text}")

        # 미리보기 업데이트
        self.update_preview()


    def on_select_target(self):
        """대상 디렉토리 선택"""
        self.target_directory = filedialog.askdirectory(title="대상 디렉토리 선택")

        if self.target_directory:
            self.target_label.config(text=f"대상 디렉토리: {self.target_directory}")

        self.update_preview()

    def update_preview(self):
        """미리보기 리스트 업데이트"""
        if not self.source_directories:
            return

        template = self.template_entry.get()
        apply_template_to_non_duplicate = self.apply_template_var.get() == 1
        file_pattern = self.pattern_entry.get()

        file_name_templates = apply_template(
            [Path(dir) for dir in self.source_directories], template, apply_template_to_non_duplicate, file_pattern
        )

        self.listbox_orig.delete(0, tk.END)
        self.listbox_new.delete(0, tk.END)

        for orig, new in file_name_templates.items():
            # 부모 디렉토리 이름과 파일 이름을 결합하여 표시
            parent_dir_name = orig.parent.name
            self.listbox_orig.insert(tk.END, f"{parent_dir_name}/{orig.name}")
            self.listbox_new.insert(tk.END, new)


    def on_start_copy(self):
        """파일 복사 실행"""
        if not self.source_directories:
            messagebox.showwarning("경고", "소스 디렉토리를 선택하지 않았습니다.")
            return
        if not self.target_directory:
            messagebox.showinfo("알림", "대상 디렉토리가 선택되지 않았습니다.")
            return

        template = self.template_entry.get()
        apply_template_to_non_duplicate = self.apply_template_var.get() == 1
        file_pattern = self.pattern_entry.get()

        copy_files_to_target(
            [Path(dir) for dir in self.source_directories], Path(self.target_directory), template, apply_template_to_non_duplicate, file_pattern
        )

    def on_close(self):
        """창 닫기 이벤트"""
        self.root.destroy()
        import sys
        sys.exit(0)


def main():
    root = tk.Tk()
    app = FileRenameApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
