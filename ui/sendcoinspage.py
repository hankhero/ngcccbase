import collections

from PyQt4 import QtGui, uic

from wallet import wallet


class SendcoinsEntry(QtGui.QFrame):
    def __init__(self, page):
        QtGui.QFrame.__init__(self)
        uic.loadUi(uic.getUiPath('sendcoinsentry.ui'), self)
        self.page = page

        self.edtAddress.focusInEvent = lambda *args: self.edtAddress.setStyleSheet('')
        self.edtAmount.focusInEvent = lambda *args: self.edtAmount.setStyleSheet('')
        self.cbMoniker.activated.connect(self.updateAvailableBalance)
        self.btnPaste.clicked.connect(self.btnPasteClicked)
        self.btnDelete.clicked.connect(self.btnDeleteClicked)

        self.update()

    def update(self):
        monikers = wallet.get_all_monikers()
        monikers.remove('bitcoin')
        monikers = ['bitcoin'] + monikers
        comboList = self.cbMoniker
        currentMoniker = str(comboList.currentText())
        comboList.clear()
        comboList.addItems(monikers)
        if currentMoniker and currentMoniker in monikers:
            comboList.setCurrentIndex(monikers.index(currentMoniker))
        self.updateAvailableBalance()

    def updateAvailableBalance(self):
        moniker = str(self.cbMoniker.currentText())
        if moniker:
            asset = wallet.get_asset_definition(moniker)
            balance = wallet.get_balance(moniker)
            self.edtAmount.setMaximum(balance)
            if moniker == 'bitcoin':
                moniker = 'BTC'
            self.lblAvailaleBalance.setText(
                '%s %s' % (asset.format_value(balance), moniker))

    def btnPasteClicked(self):
        self.edtAddress.setText(QtGui.QApplication.clipboard().text())

    def btnDeleteClicked(self):
        self.close()
        self.page.entries.takeAt(self.page.entries.indexOf(self))
        self.page.entries.itemAt(0).widget().btnDelete.setEnabled(
            self.page.entries.count() > 1)

    def edtAddressValidate(self):
        valid = True
        if len(str(self.edtAddress.text())) != 34:
            valid = False
            self.edtAddress.setStyleSheet('background:#FF8080')
        else:
            self.edtAddress.setStyleSheet('')
        return valid

    def edtAmountValidate(self):
        valid = True
        if self.edtAmount.value() == 0:
            valid = False
            self.edtAmount.setStyleSheet('background:#FF8080')
        else:
            self.edtAmount.setStyleSheet('')
        return valid

    def isValid(self):
        return all([self.edtAddressValidate(), self.edtAmountValidate()])

    def getData(self):
        return {
            'address': str(self.edtAddress.text()),
            'value':   self.edtAmount.value(),
            'moniker': str(self.cbMoniker.currentText()),
        }


class SendcoinsPage(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        uic.loadUi(uic.getUiPath('sendcoinspage.ui'), self)

        self.btnAddRecipient.clicked.connect(self.btnAddRecipientClicked)
        self.btnClearAll.clicked.connect(self.btnClearAllClicked)
        self.btnSend.clicked.connect(self.btnSendClicked)

        self.btnAddRecipientClicked()

    def update(self):
        for i in xrange(self.entries.count()):
            self.entries.itemAt(i).widget().update()

    def btnAddRecipientClicked(self):
        self.entries.addWidget(SendcoinsEntry(self))
        self.entries.itemAt(0).widget().btnDelete.setEnabled(
            self.entries.count() > 1)

    def btnClearAllClicked(self):
        while True:
            layout = self.entries.takeAt(0)
            if layout is None:
                break
            layout.widget().close()
        self.btnAddRecipientClicked()

    def btnSendClicked(self):
        entries = [self.entries.itemAt(i).widget()
                    for i in xrange(self.entries.count())]
        if not all([entry.isValid() for entry in entries]):
            return
        data = [entry.getData() for entry in entries]
        message = 'Are you sure you want to send'
        for recipient in data:
            if recipient['moniker'] == 'bitcoin':
                tpl = '<br><b>{value} BTC</b> to {address}'
            else:
                tpl = '<br><b>{value} {moniker}</b> to {address}'
            message += tpl.format(**recipient)
        message += '?'
        retval = QtGui.QMessageBox.question(
            self, 'Confirm send coins',
            message,
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
            QtGui.QMessageBox.Cancel)
        if retval != QtGui.QMessageBox.Yes:
            return
        # check value exceeds balance
        currency = collections.defaultdict(float)
        for recipient in data:
            currency[recipient['moniker']] += recipient['value']
        for moniker, value in currency.items():
            # TODO: fix value
            if value > wallet.get_balance(moniker)/1e8:
                QtGui.QMessageBox.warning(
                    self, 'Send coins',
                    'The amount for <b>%s</b> exceeds your balance.' % moniker,
                    QtGui.QMessageBox.Ok)
                return
        # TODO: fix send coins
        wallet.send_coins(data)

