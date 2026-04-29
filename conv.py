import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class CurrencyConverter:
    """Main application class"""
    
    # Common currencies
    CURRENCIES = [
        "USD", "EUR", "RUB", "GBP", "JPY", "CNY", "TRY", "CAD", 
        "AUD", "CHF", "INR", "BRL", "MXN", "KRW", "SGD", "NOK",
        "SEK", "NZD", "ZAR", "AED", "SAR", "PLN", "THB", "HKD"
    ]
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Конвертер валют")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # API configuration
        self.api_key = None
        self.api_url = "https://v6.exchangerate-api.com/v6/{}/latest/{}"
        
        # Data storage
        self.history_file = "conversion_history.json"
        self.history: List[Dict] = self.load_history()
        
        # Setup UI
        self.setup_ui()
        
        # Load currencies from API
        self.root.after(100, self.load_currencies_from_api)
        
    def setup_ui(self):
        """Initialize all UI components"""
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # API Key section
        api_frame = ttk.LabelFrame(main_frame, text="API Настройки", padding="10")
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(api_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        self.api_entry = ttk.Entry(api_frame, width=35, show="*")
        self.api_entry.pack(side=tk.LEFT, padx=5)
        self.api_entry.insert(0, "YOUR_API_KEY_HERE")  # Replace with your key
        
        ttk.Button(api_frame, text="Сохранить API ключ", 
                  command=self.save_api_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(api_frame, text="Получить бесплатный ключ", 
                  command=self.open_api_website).pack(side=tk.LEFT, padx=5)
        
        # Conversion section
        conv_frame = ttk.LabelFrame(main_frame, text="Конвертация", padding="15")
        conv_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Amount input
        amount_frame = ttk.Frame(conv_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        ttk.Label(amount_frame, text="Сумма:", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        self.amount_entry = ttk.Entry(amount_frame, width=20, font=('Arial', 11))
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        
        # Currency selection
        currency_frame = ttk.Frame(conv_frame)
        currency_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(currency_frame, text="Из валюты:", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        self.from_currency = ttk.Combobox(currency_frame, values=self.CURRENCIES, width=10, font=('Arial', 11))
        self.from_currency.pack(side=tk.LEFT, padx=5)
        self.from_currency.set("USD")
        
        ttk.Label(currency_frame, text="→", font=('Arial', 14)).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(currency_frame, text="В валюту:", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        self.to_currency = ttk.Combobox(currency_frame, values=self.CURRENCIES, width=10, font=('Arial', 11))
        self.to_currency.pack(side=tk.LEFT, padx=5)
        self.to_currency.set("EUR")
        
        # Convert button
        self.convert_btn = ttk.Button(conv_frame, text="Конвертировать", 
                                      command=self.convert_currency, style="Accent.TButton")
        self.convert_btn.pack(pady=10)
        
        # Result display
        result_frame = ttk.Frame(conv_frame)
        result_frame.pack(fill=tk.X, pady=10)
        self.result_label = ttk.Label(result_frame, text="", font=('Arial', 20, 'bold'), foreground='green')
        self.result_label.pack()
        
        # Rate info
        self.rate_label = ttk.Label(result_frame, text="", font=('Arial', 10), foreground='gray')
        self.rate_label.pack()
        
        # History section
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filter controls
        filter_frame = ttk.Frame(history_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Фильтр по валюте:").pack(side=tk.LEFT, padx=5)
        self.filter_currency = ttk.Combobox(filter_frame, values=self.CURRENCIES + [""], width=10)
        self.filter_currency.pack(side=tk.LEFT, padx=5)
        self.filter_currency.set("")
        
        ttk.Button(filter_frame, text="Применить фильтр", 
                  command=self.apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Сбросить фильтр", 
                  command=self.reset_filter).pack(side=tk.LEFT, padx=5)
        
        # Treeview for history
        columns = ('id', 'timestamp', 'amount', 'from_curr', 'to_curr', 'rate', 'result')
        self.tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=12)
        
        self.tree.heading('id', text='№')
        self.tree.heading('timestamp', text='Дата/время')
        self.tree.heading('amount', text='Сумма')
        self.tree.heading('from_curr', text='Из')
        self.tree.heading('to_curr', text='В')
        self.tree.heading('rate', text='Курс')
        self.tree.heading('result', text='Результат')
        
        self.tree.column('id', width=50)
        self.tree.column('timestamp', width=150)
        self.tree.column('amount', width=100)
        self.tree.column('from_curr', width=80)
        self.tree.column('to_curr', width=80)
        self.tree.column('rate', width=100)
        self.tree.column('result', width=120)
        
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="Очистить историю", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Экспорт истории (JSON)", 
                  command=self.export_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Обновить курсы", 
                  command=self.update_rates).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе. Введите API ключ для начала.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Load existing history
        self.refresh_history_display()
        
    def save_api_key(self):
        """Save API key to file"""
        self.api_key = self.api_entry.get().strip()
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            messagebox.showerror("Ошибка", "Введите корректный API ключ")
            return
            
        try:
            with open("api_key.txt", "w") as f:
                f.write(self.api_key)
            messagebox.showinfo("Успех", "API ключ сохранён")
            self.status_var.set("API ключ сохранён. Используйте Конвертировать для теста.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить ключ: {str(e)}")
            
    def load_api_key(self) -> Optional[str]:
        """Load API key from file"""
        if os.path.exists("api_key.txt"):
            try:
                with open("api_key.txt", "r") as f:
                    return f.read().strip()
            except:
                pass
        return None
        
    def open_api_website(self):
        """Open exchangerate-api.com website"""
        import webbrowser
        webbrowser.open("https://www.exchangerate-api.com/")
        
    def load_currencies_from_api(self):
        """Load available currencies from API (optional enhancement)"""
        # Using predefined list as fallback
        pass
        
    def get_exchange_rate(self, from_curr: str, to_curr: str) -> Optional[float]:
        """Get exchange rate from external API"""
        if not self.api_key:
            self.api_key = self.load_api_key()
            if self.api_key:
                self.api_entry.delete(0, tk.END)
                self.api_entry.insert(0, self.api_key)
                
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            messagebox.showerror("Ошибка", 
                                "API ключ не настроен.\n"
                                "1. Получите бесплатный ключ на exchangerate-api.com\n"
                                "2. Введите его в поле выше\n"
                                "3. Нажмите 'Сохранить API ключ'")
            return None
            
        try:
            url = self.api_url.format(self.api_key, from_curr)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('result') == 'success':
                    rates = data.get('conversion_rates', {})
                    if to_curr in rates:
                        return rates[to_curr]
                    else:
                        messagebox.showerror("Ошибка", f"Валюта {to_curr} не найдена")
                        return None
                else:
                    error_msg = data.get('error-type', 'unknown')
                    messagebox.showerror("Ошибка API", f"Ошибка: {error_msg}")
                    return None
            else:
                messagebox.showerror("Ошибка сети", f"HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            messagebox.showerror("Ошибка", "Превышено время ожидания ответа от API")
            return None
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к интернету")
            return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {str(e)}")
            return None
            
    def validate_amount(self, amount_str: str) -> Optional[float]:
        """Validate amount input"""
        if not amount_str:
            messagebox.showerror("Ошибка ввода", "Введите сумму")
            return None
            
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Ошибка ввода", "Сумма должна быть положительным числом")
                return None
            if amount > 1e12:
                messagebox.showerror("Ошибка ввода", "Сумма слишком большая")
                return None
            return amount
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Введите корректное число")
            return None
            
    def convert_currency(self):
        """Perform currency conversion and save to history"""
        # Validate amount
        amount = self.validate_amount(self.amount_entry.get().strip())
        if amount is None:
            return
            
        from_curr = self.from_currency.get().strip().upper()
        to_curr = self.to_currency.get().strip().upper()
        
        if not from_curr or not to_curr:
            messagebox.showerror("Ошибка", "Выберите обе валюты")
            return
            
        # Get exchange rate
        rate = self.get_exchange_rate(from_curr, to_curr)
        if rate is None:
            return
            
        # Calculate result
        result = amount * rate
        
        # Display result
        self.result_label.config(text=f"{result:.2f} {to_curr}")
        self.rate_label.config(text=f"Курс: 1 {from_curr} = {rate:.4f} {to_curr}")
        
        # Save to history
        history_entry = {
            'id': len(self.history) + 1,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'amount': amount,
            'from_curr': from_curr,
            'to_curr': to_curr,
            'rate': rate,
            'result': round(result, 2)
        }
        
        self.history.append(history_entry)
        self.save_history()
        self.refresh_history_display()
        
        self.status_var.set(f"Конвертация выполнена: {amount} {from_curr} → {result:.2f} {to_curr}")
        
    def save_history(self):
        """Save conversion history to JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {str(e)}")
            
    def load_history(self) -> List[Dict]:
        """Load history from JSON file"""
        if not os.path.exists(self.history_file):
            return []
            
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
            
    def refresh_history_display(self):
        """Update treeview with filtered history"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        filter_curr = self.filter_currency.get().strip().upper()
        filtered_history = self.history
        
        if filter_curr:
            filtered_history = [h for h in self.history 
                              if h['from_curr'] == filter_curr or h['to_curr'] == filter_curr]
            
        for item in filtered_history:
            self.tree.insert('', tk.END, values=(
                item['id'],
                item['timestamp'],
                f"{item['amount']:.2f}",
                item['from_curr'],
                item['to_curr'],
                f"{item['rate']:.4f}",
                f"{item['result']:.2f}"
            ))
            
    def apply_filter(self):
        """Apply currency filter"""
        self.refresh_history_display()
        
    def reset_filter(self):
        """Reset filter"""
        self.filter_currency.set("")
        self.refresh_history_display()
        
    def clear_history(self):
        """Clear all history with confirmation"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.save_history()
            self.refresh_history_display()
            self.status_var.set("История очищена")
            
    def export_history(self):
        """Export history to JSON file"""
        if not self.history:
            messagebox.showinfo("Информация", "Нет данных для экспорта")
            return
            
        filename = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"История экспортирована в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")
            
    def update_rates(self):
        """Manual rate update (just for show, rates are fetched on conversion)"""
        messagebox.showinfo("Информация", "Курсы обновляются автоматически при каждой конвертации")


def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()