import customtkinter as ctk
import subprocess
import threading
import os
from tkinter import filedialog, scrolledtext, messagebox
import re
from CTkTable import CTkTable
import sys
import shutil

def check_command_exists(command):
    """명령어가 시스템에 설치되어 있는지 확인"""
    return shutil.which(command) is not None

def install_with_winget(package_name, display_name, log_callback=None):
    """winget을 사용하여 패키지 설치"""
    try:
        if log_callback:
            log_callback(f"{display_name} 설치 중...")
        result = subprocess.run(
            ["winget", "install", "--id", package_name, "--accept-source-agreements", "--accept-package-agreements"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        if result.returncode == 0:
            if log_callback:
                log_callback(f"✅ {display_name} 설치 완료!")
            return True
        else:
            if log_callback:
                log_callback(f"❌ {display_name} 설치 실패: {result.stderr}")
            return False
    except Exception as e:
        if log_callback:
            log_callback(f"❌ {display_name} 설치 중 오류: {str(e)}")
        return False

def update_ytdlp(log_callback=None):
    """yt-dlp 업데이트"""
    try:
        if log_callback:
            log_callback("yt-dlp 업데이트 확인 중...")
        result = subprocess.run(
            ["yt-dlp", "-U"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        if "Updated" in result.stdout or "up to date" in result.stdout:
            if log_callback:
                log_callback("✅ yt-dlp가 최신 버전입니다.")
        return True
    except Exception as e:
        if log_callback:
            log_callback(f"⚠️ yt-dlp 업데이트 확인 실패: {str(e)}")
        return False

def check_dependencies(log_callback=None):
    """필수 의존성 체크 및 자동 설치"""
    if log_callback:
        log_callback("=" * 60)
        log_callback("의존성 확인 중...")
        log_callback("=" * 60)

    newly_installed = False

    # yt-dlp 체크
    if not check_command_exists("yt-dlp"):
        if log_callback:
            log_callback("⚠️ yt-dlp가 설치되어 있지 않습니다.")
        if not install_with_winget("yt-dlp.yt-dlp", "yt-dlp", log_callback):
            return False, False
        newly_installed = True
    else:
        if log_callback:
            log_callback("✅ yt-dlp 설치 확인")
        # yt-dlp 업데이트 확인
        update_ytdlp(log_callback)

    if log_callback:
        log_callback("=" * 60)
        log_callback("모든 의존성 확인 완료!")
        log_callback("=" * 60)
    return True, newly_installed

class VRDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.title("YouTube VR 영상 다운로더")
        self.geometry("600x700")

        # 다운로드 경로 기본값
        self.download_path = os.path.expanduser("~/Downloads")

        # 선택된 포맷 저장
        self.selected_video = None
        self.selected_audio = None

        # 의존성 체크 완료 플래그
        self.dependencies_ready = False

        # UI 구성
        self.setup_ui()

        # 백그라운드에서 의존성 체크
        self.start_dependency_check()

    def setup_ui(self):
        # 메인 프레임
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # 테이블 영역
        self.grid_rowconfigure(5, weight=1)  # 로그 영역

        # URL 입력 섹션
        url_frame = ctk.CTkFrame(self)
        url_frame.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        url_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text="YouTube URL:", font=("", 14, "bold")).grid(
            row=0, column=0, padx=10, pady=8, sticky="w"
        )

        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="YouTube VR 영상 URL을 입력하세요")
        self.url_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        self.paste_btn = ctk.CTkButton(
            url_frame, text="붙여넣기", command=self.paste_and_list, width=100, state="disabled"
        )
        self.paste_btn.grid(row=0, column=2, padx=(10, 5), pady=8)

        self.list_formats_btn = ctk.CTkButton(
            url_frame, text="포맷 목록 확인", command=self.list_formats, width=120, state="disabled"
        )
        self.list_formats_btn.grid(row=0, column=3, padx=(5, 10), pady=8)

        # 다운로드 경로 섹션
        path_frame = ctk.CTkFrame(self)
        path_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        path_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(path_frame, text="저장 경로:", font=("", 14, "bold")).grid(
            row=0, column=0, padx=10, pady=8, sticky="w"
        )

        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            path_frame, text="찾아보기", command=self.browse_path, width=100, state="disabled"
        )
        self.browse_btn.grid(row=0, column=2, padx=10, pady=8)

        # 포맷 선택 섹션
        format_frame = ctk.CTkFrame(self)
        format_frame.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        format_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(format_frame, text="포맷 선택:", font=("", 14, "bold")).grid(
            row=0, column=0, padx=10, pady=8, sticky="w"
        )

        self.format_entry = ctk.CTkEntry(format_frame, placeholder_text="예: bv+ba 또는 137+140")
        self.format_entry.insert(0, "bv+ba")
        self.format_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        self.download_btn = ctk.CTkButton(
            format_frame, text="다운로드", command=self.download_video,
            width=120, fg_color="green", hover_color="darkgreen", state="disabled"
        )
        self.download_btn.grid(row=0, column=2, padx=10, pady=8)

        # 포맷 테이블 섹션 (처음엔 숨김)
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=3, column=0, padx=15, pady=5, sticky="nsew")
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.table_frame, text="사용 가능한 포맷 (클릭하여 선택):", font=("", 14, "bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )

        # CTkTable 초기화 (헤더만)
        self.format_table_data = [
            ["ID", "확장자", "해상도", "크기", "비디오", "오디오", "속성"]
        ]

        self.format_table = CTkTable(
            self.table_frame,
            row=1,
            column=7,
            values=self.format_table_data,
            hover_color="#2b2b2b",
            header_color="#1f538d",
            corner_radius=8
        )
        self.format_table.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # 처음엔 테이블 숨김
        self.table_frame.grid_remove()

        # 진행 상황 표시
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(
            progress_frame, text="대기 중...", font=("", 12)
        )
        self.progress_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.set(0)

        # 로그 출력 섹션
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=5, column=0, padx=15, pady=(5, 15), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_frame, text="출력 로그:", font=("", 14, "bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )

        # CustomTkinter의 textbox 사용 (monospace 폰트 적용)
        self.log_text = ctk.CTkTextbox(log_frame, wrap="word", height=200, font=("Consolas", 11))
        self.log_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def start_dependency_check(self):
        """백그라운드에서 의존성 체크 시작"""
        self.progress_label.configure(text="의존성 확인 중...")
        self.progress_bar.set(0.3)
        self.log_message("🔧 프로그램 시작 - 필수 도구 확인 중...")

        def run_check():
            try:
                success, newly_installed = check_dependencies(log_callback=self.log_message)

                if success:
                    self.dependencies_ready = True
                    self.progress_bar.set(1.0)
                    self.progress_label.configure(text="준비 완료!")

                    if newly_installed:
                        # yt-dlp를 새로 설치한 경우 재시작 필요 메시지
                        self.log_message("\n" + "=" * 60)
                        self.log_message("⚠️ yt-dlp 설치가 완료되었습니다!")
                        self.log_message("⚠️ 프로그램을 종료하고 다시 실행해주세요!")
                        self.log_message("=" * 60 + "\n")

                        messagebox.showwarning(
                            "재시작 필요",
                            "yt-dlp 설치가 완료되었습니다.\n\n"
                            "프로그램을 종료하고 다시 실행해주세요.\n\n"
                            "확인 버튼을 누르면 프로그램이 종료됩니다."
                        )
                        self.quit()
                    else:
                        self.log_message("\n✅ 프로그램 사용 준비 완료!\n")

                        # UI 버튼 활성화
                        self.paste_btn.configure(state="normal")
                        self.list_formats_btn.configure(state="normal")
                        self.browse_btn.configure(state="normal")
                        self.download_btn.configure(state="normal")

                        # 잠시 후 진행 바 리셋
                        self.after(1000, lambda: self.progress_bar.set(0))
                        self.after(1000, lambda: self.progress_label.configure(text="대기 중..."))
                else:
                    self.progress_bar.set(0)
                    self.progress_label.configure(text="의존성 체크 실패")
                    self.log_message("\n❌ 필수 도구 설치에 실패했습니다.")
                    messagebox.showerror("오류", "yt-dlp 설치에 실패했습니다.\n수동으로 설치해주세요.")
            except Exception as e:
                self.progress_bar.set(0)
                self.progress_label.configure(text="오류 발생")
                self.log_message(f"\n❌ 오류: {str(e)}")
                messagebox.showerror("오류", f"의존성 확인 중 오류가 발생했습니다:\n{str(e)}")

        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
            self.download_path = path
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def paste_and_list(self):
        """클립보드에서 URL 붙여넣기 후 포맷 목록 확인"""
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clipboard_text.strip())
                self.log_message(f"📋 URL 붙여넣기 완료")
                # 포맷 목록 자동 확인
                self.list_formats()
            else:
                self.log_message("❌ 클립보드가 비어있습니다.")
        except Exception as e:
            self.log_message(f"❌ 붙여넣기 실패: {str(e)}")

    def log_message(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def parse_format_table(self, output):
        """포맷 목록을 파싱하여 리스트 데이터로 반환"""
        lines = output.split('\n')
        formats = []

        # [info] Available formats 라인 찾기
        start_idx = -1
        for i, line in enumerate(lines):
            if '[info] Available formats' in line:
                start_idx = i + 1
                break

        if start_idx == -1:
            return output

        # 헤더와 구분선 건너뛰기
        data_start = start_idx + 2 if start_idx + 2 < len(lines) else start_idx

        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith('['):
                continue

            # 각 포맷 라인 파싱
            parts = line.split()
            if len(parts) < 3:
                continue

            format_id = parts[0]
            ext = parts[1]

            # mhtml 제외
            if ext == 'mhtml':
                continue

            # 오디오 전용 체크
            is_audio = 'audio only' in line

            # 해상도 파싱
            if is_audio:
                resolution = "오디오"
            else:
                resolution = parts[2]

                # FHD(1920x1080) 이하 해상도 필터링
                try:
                    if 'x' in resolution:
                        width, height = map(int, resolution.split('x'))
                        # 1920x1080 이하는 제외 (초과만 표시)
                        if width <= 1920 and height <= 1080:
                            continue
                except:
                    pass

            # 파일 크기 파싱
            size = ""
            for part in parts:
                if 'MiB' in part or 'GiB' in part or 'KiB' in part:
                    size = part
                    break

            # 비디오/오디오 코덱 정보
            vcodec = ""
            acodec = ""

            if 'avc1' in line:
                vcodec = "H.264"
            elif 'vp9' in line:
                vcodec = "VP9"
            elif 'av01' in line:
                vcodec = "AV1"

            if 'mp4a' in line:
                acodec = "AAC"
            elif 'opus' in line:
                acodec = "Opus"

            # 특수 속성
            attrs = []
            if '60' in line and 'FPS' not in attrs:
                attrs.append("60fps")
            if 'mesh' in line:
                attrs.append("VR")
            if 'ambisonics' in line:
                attrs.append("입체음향")

            formats.append({
                'id': format_id,
                'ext': ext,
                'resolution': resolution,
                'size': size,
                'vcodec': vcodec,
                'acodec': acodec,
                'attrs': ' '.join(attrs)
            })

        # 리스트 데이터 생성
        if not formats:
            return []

        table_data = []
        for fmt in formats:
            table_data.append([
                fmt['id'],
                fmt['ext'],
                fmt['resolution'],
                fmt['size'],
                fmt['vcodec'],
                fmt['acodec'],
                fmt['attrs']
            ])

        return table_data

    def update_format_table(self, data):
        """테이블 데이터 업데이트"""
        # 헤더 + 데이터
        header = [["ID", "확장자", "해상도", "크기", "비디오", "오디오", "속성"]]
        self.format_table_data = header + data

        # 테이블 재생성
        self.format_table.destroy()

        self.format_table = CTkTable(
            self.table_frame,
            row=len(self.format_table_data),
            column=7,
            values=self.format_table_data,
            hover_color="#2b2b2b",
            header_color="#1f538d",
            corner_radius=8,
            command=self.on_format_click
        )
        self.format_table.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # 테이블 프레임 보이기
        self.table_frame.grid()

    def on_format_click(self, cell):
        """테이블 셀 클릭 이벤트"""
        row = cell["row"]
        column = cell["column"]

        # 헤더 클릭 무시
        if row == 0:
            return

        # ID 열(첫 번째 열) 값 가져오기
        format_id = self.format_table_data[row][0]
        resolution = self.format_table_data[row][2]

        # 오디오인지 비디오인지 구분
        if resolution == "오디오":
            self.selected_audio = format_id
            self.log_message(f"✅ 오디오 선택됨: {format_id}")
        else:
            self.selected_video = format_id
            self.log_message(f"✅ 비디오 선택됨: {format_id}")

        # 포맷 입력 필드 업데이트
        self.format_entry.delete(0, "end")
        if self.selected_video and self.selected_audio:
            self.format_entry.insert(0, f"{self.selected_video}+{self.selected_audio}")
        elif self.selected_video:
            self.format_entry.insert(0, self.selected_video)
        elif self.selected_audio:
            self.format_entry.insert(0, self.selected_audio)

    def list_formats(self):
        url = self.url_entry.get().strip()
        if not url:
            self.log_message("❌ URL을 입력하세요.")
            return

        self.log_message(f"📋 포맷 목록 확인 중...\n")
        self.progress_label.configure(text="포맷 목록 확인 중...")
        self.progress_bar.set(0.5)
        self.list_formats_btn.configure(state="disabled")

        def run_list_formats():
            try:
                cmd = [
                    "yt-dlp",
                    "--extractor-args", "youtube:player-client=android_vr",
                    "--list-formats",
                    url
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )

                if result.returncode == 0:
                    table_data = self.parse_format_table(result.stdout)
                    if table_data:
                        self.update_format_table(table_data)
                        self.log_message(f"✅ {len(table_data)}개의 포맷을 찾았습니다. 테이블에서 클릭하여 선택하세요.")
                    else:
                        self.log_message("❌ 사용 가능한 포맷이 없습니다.")
                else:
                    self.log_message(f"❌ 오류 발생:\n{result.stderr}")

            except Exception as e:
                self.log_message(f"❌ 예외 발생: {str(e)}")
            finally:
                self.progress_bar.set(0)
                self.progress_label.configure(text="대기 중...")
                self.list_formats_btn.configure(state="normal")

        thread = threading.Thread(target=run_list_formats, daemon=True)
        thread.start()

    def download_video(self):
        url = self.url_entry.get().strip()
        format_str = self.format_entry.get().strip()
        download_path = self.path_entry.get().strip()

        if not url:
            self.log_message("❌ URL을 입력하세요.")
            return

        if not format_str:
            format_str = "bv+ba"

        self.log_message(f"⬇️ 다운로드 시작: {url}")
        self.log_message(f"📁 저장 경로: {download_path}")
        self.log_message(f"🎬 포맷: {format_str}\n")
        self.progress_label.configure(text="다운로드 준비 중...")
        self.progress_bar.set(0)
        self.download_btn.configure(state="disabled")

        def run_download():
            try:
                cmd = [
                    "yt-dlp",
                    "--extractor-args", "youtube:player-client=android_vr",
                    "-f", format_str,
                    "-o", os.path.join(download_path, "%(title)s.%(ext)s"),
                    "--progress",
                    "--newline",
                    url
                ]

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )

                downloading_started = False
                for line in process.stdout:
                    line = line.strip()
                    if not line:
                        continue

                    # 다운로드 진행률 라인 필터링
                    if "[download]" in line and "%" in line:
                        # 진행률 파싱 및 프로그레스바 업데이트
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            try:
                                percent = float(match.group(1)) / 100
                                self.progress_bar.set(percent)

                                # 속도와 ETA 파싱
                                speed_match = re.search(r'at\s+([0-9.]+\s*[KMG]iB/s)', line)
                                eta_match = re.search(r'ETA\s+(\d+:\d+)', line)

                                speed = speed_match.group(1) if speed_match else "계산 중"
                                eta = eta_match.group(1) if eta_match else "계산 중"

                                self.progress_label.configure(
                                    text=f"다운로드 중... {percent*100:.1f}% | 속도: {speed} | 남은 시간: {eta}"
                                )
                                downloading_started = True
                            except:
                                pass
                        # 진행률 라인은 로그에 추가하지 않음
                        continue

                    # Destination 라인은 로그에 추가
                    if "[download] Destination:" in line:
                        filename = line.split("Destination:")[-1].strip()
                        self.log_message(f"💾 파일명: {filename}")
                        continue

                    # Sleeping 라인은 간단하게 표시
                    if "Sleeping" in line:
                        self.log_message("⏳ 잠시 대기 중...")
                        continue

                    # Extracting, Downloading 등 주요 이벤트만 로그에 추가
                    if any(keyword in line for keyword in ["[youtube]", "[info]", "Merging", "Deleting"]):
                        # 너무 상세한 정보는 제외
                        if "Downloading" in line and "API JSON" in line:
                            continue
                        if "Extracting" in line:
                            self.log_message("🔍 영상 정보 추출 중...")
                        elif "Merging" in line:
                            self.log_message("🔧 영상과 오디오 병합 중...")
                        elif "[info]" in line and "format(s)" in line:
                            self.log_message(line.replace("[info]", "📥"))
                        else:
                            # 기타 중요 메시지
                            if len(line) < 200:  # 너무 긴 메시지 제외
                                self.log_message(line)

                process.wait()

                if process.returncode == 0:
                    self.log_message("\n✅ 다운로드 완료!")
                    self.progress_bar.set(1.0)
                    self.progress_label.configure(text="다운로드 완료!")
                else:
                    self.log_message(f"\n❌ 다운로드 실패 (코드: {process.returncode})")
                    self.progress_bar.set(0)
                    self.progress_label.configure(text="다운로드 실패")

            except Exception as e:
                self.log_message(f"❌ 예외 발생: {str(e)}")
                self.progress_bar.set(0)
                self.progress_label.configure(text="오류 발생")
            finally:
                self.download_btn.configure(state="normal")

        thread = threading.Thread(target=run_download, daemon=True)
        thread.start()

if __name__ == "__main__":
    # CustomTkinter 테마 설정
    ctk.set_appearance_mode("dark")  # "dark", "light", "system"
    ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

    app = VRDownloaderApp()
    app.mainloop()
