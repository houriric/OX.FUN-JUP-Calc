import asyncio
import sys
from collections import defaultdict
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor

from config import ASSETS
from OX_Code.Price_Feed.Final_Code.BidAskListSimAuth import fetch_ox_prices, latest_data as ox_data
from Jup.Price_Feed.Jup_Price_Feed import fetch_jupiter_prices, latest_data as jupiter_data

class PriceComparisonGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Price Comparison")
        self.setGeometry(100, 100, 1200, 600)  # Increased width to accommodate new column

        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)  # Increased column count
        self.table.setHorizontalHeaderLabels(['Asset', 'OX Price', 'Jupiter Price', 'Difference', 'Percentage', 'OX Spread ($)', 'OX Spread (%)', 'Opportunity'])
        
        layout.addWidget(self.table)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(100)  # Update every 100ms

    def update_table(self):
        price_data = []
        for asset in ASSETS:
            ox_ask = ox_data[asset['ox_code']].get('ask')
            ox_bid = ox_data[asset['ox_code']].get('bid')
            jupiter_price = jupiter_data[asset['jupiter_code']].get('price')
            
            if ox_ask and ox_bid and jupiter_price:
                ox_ask = float(ox_ask)
                ox_bid = float(ox_bid)
                jupiter_price = float(jupiter_price)
                difference = ox_ask - jupiter_price
                percentage = (difference / jupiter_price) * 100
                ox_spread_dollar = ox_ask - ox_bid
                ox_spread_percent = (ox_spread_dollar / ox_bid) * 100
                price_data.append((asset['name'], ox_ask, jupiter_price, difference, percentage, ox_spread_dollar, ox_spread_percent))
        
        # Sort by percentage difference, descending order
        price_data.sort(key=lambda x: x[4], reverse=True)
        
        self.table.setRowCount(len(price_data))
        for row, data in enumerate(price_data):
            self.table.setItem(row, 0, QTableWidgetItem(data[0]))
            self.table.setItem(row, 1, QTableWidgetItem(f"${data[1]:.6f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"${data[2]:.6f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"${data[3]:.6f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{data[4]:.2f}%"))
            self.table.setItem(row, 5, QTableWidgetItem(f"${data[5]:.6f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{data[6]:.2f}%"))
            
            opportunity = "Short" if data[4] > 0 else "Long"
            opportunity_item = QTableWidgetItem(opportunity)
            opportunity_item.setForeground(QColor('green' if opportunity == "Short" else 'red'))
            self.table.setItem(row, 7, opportunity_item)
        
        self.table.resizeColumnsToContents()

async def fetch_data():
    ox_task = asyncio.create_task(fetch_ox_prices())
    jupiter_task = asyncio.create_task(fetch_jupiter_prices())
    await asyncio.gather(ox_task, jupiter_task)

def run_gui():
    app = QApplication(sys.argv)
    window = PriceComparisonGUI()
    window.show()
    sys.exit(app.exec_())

async def main():
    data_task = asyncio.create_task(fetch_data())
    gui_task = asyncio.to_thread(run_gui)
    await asyncio.gather(data_task, gui_task)

if __name__ == "__main__":
    asyncio.run(main())