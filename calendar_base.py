import datetime


class _BaseCalendar:
    '''
    The Base for all calendar types ( Exchange, AdAstra )
    Dont use this class directly, instead subclass it.
    '''

    def __init__(self):
        self._connectionStatus = None
        self._Connected = None
        self._Disconnected = None

        self._CalendarItemDeleted = None  # callback for when an item is deleted
        self._CalendarItemChanged = None  # callback for when an item is changed
        self._NewCalendarItem = None  # callback for when an item is created

        self._calendarItems = []  # list of _CalendarItem object

    @property
    def NewCalendarItem(self):
        return self._NewCalendarItem

    @NewCalendarItem.setter
    def NewCalendarItem(self, func):
        self._NewCalendarItem = func

    ##############
    @property
    def CalendarItemChanged(self):
        return self._CalendarItemChanged

    @CalendarItemChanged.setter
    def CalendarItemChanged(self, func):
        self._CalendarItemChanged = func

    ############
    @property
    def CalendarItemDeleted(self):
        return self._CalendarItemDeleted

    @CalendarItemDeleted.setter
    def CalendarItemDeleted(self, func):
        self._CalendarItemDeleted = func

    ############
    @property
    def Connected(self):
        return self._Connected

    @Connected.setter
    def Connected(self, func):
        self._Connected = func

    #############
    @property
    def Disconnected(self):
        return self._Disconnected

    @Disconnected.setter
    def Disconnected(self, func):
        self._Disconnected = func

    def _NewConnectionStatus(self, state):
        print('378 _NewConnectionStatus(', state, ', self._connectionStatus=', self._connectionStatus)
        if state != self._connectionStatus:
            # the connection status has changed
            self._connectionStatus = state
            if state == 'Connected':
                if callable(self._Connected):
                    self._Connected(self, state)
            elif state == 'Disconnected':
                if callable(self._Disconnected):
                    self._Disconnected(self, state)

    def UpdateCalendar(self, calendar=None, startDT=None, endDT=None):
        '''
        Subclasses should override this

        :param calendar: a particular calendar ( None means use the default calendar)
        :param startDT: only search for events after this date
        :param endDT: only search for events before this date
        :return:
        '''
        pass

    def CreateCalendarEvent(self, subject, body, startDT, endDT):
        '''
        Subclasses should override this

        Create a new calendar item with the above info

        :param subject:
        :param body:
        :param startDT:
        :param endDT:
        :return:
        '''
        pass

    def ChangeEventTime(self, calItem, newStartDT, newEndDT):
        '''
        Subclasses should override this

        Changes the time of a current event

        :param calItem:
        :param newStartDT:
        :param newEndDT:
        :return:
        '''

    def DeleteEvent(self, calItem):
        '''
        Subclasses should override this

        Deletes an event from the server

        :param calItem:
        :return:
        '''

    # Dont override these below (unless you dare) #########################

    def GetCalendarItemsBySubject(self, exactMatch=None, partialMatch=None):
        ret = []
        for calItem in self._calendarItems:
            # print('426 searching for exactMatch={}, partialMatch={}'.format(exactMatch, partialMatch))
            if calItem.Get('Subject') == exactMatch:
                calItem = self._UpdateItemFromServer(calItem)
                ret.append(calItem)

            elif partialMatch and partialMatch in calItem.Get('Subject'):
                calItem = self._UpdateItemFromServer(calItem)
                ret.append(calItem)

        return ret

    def GetCalendarItemByID(self, itemId):
        for calItem in self._calendarItems:
            # print('424 searching for itemId={}, thisItemId={}'.format(itemId, calItem.Get('ItemId')))
            if calItem.Get('ItemId') == itemId:
                calItem = self._UpdateItemFromServer(calItem)
                return calItem

    def GetAllEvents(self):
        return self._calendarItems.copy()

    def GetEventAtTime(self, dt=None):
        # dt = datetime.date or datetime.datetime
        # return a list of events that occur on datetime.date or at datetime.datetime

        if dt is None:
            dt = datetime.datetime.now()

        events = []

        for calItem in self._calendarItems.copy():
            if dt in calItem:
                events.append(calItem)

        return events

    def GetEventsInRange(self, startDT, endDT):
        ret = []
        for item in self._calendarItems:
            if startDT <= item <= endDT:
                ret.append(item)

        return ret

    def GetNowCalItems(self):
        # returns list of calendar nowItems happening now

        returnCalItems = []

        nowDT = datetime.datetime.now()

        for calItem in self._calendarItems.copy():
            if nowDT in calItem:
                returnCalItems.append(calItem)

        return returnCalItems

    def GetNextCalItems(self):
        # return a list CalendarItems
        # will not return events happening now. only the nearest future event(s)
        # if multiple events start at the same time, all CalendarItems will be returned

        nowDT = datetime.datetime.now()

        nextStartDT = None
        for calItem in self._calendarItems.copy():
            startDT = calItem.Get('Start')
            if startDT > nowDT:  # its in the future
                if nextStartDT is None or startDT < nextStartDT:  # its sooner than the previous soonest one. (Wha!?)
                    nextStartDT = startDT

        if nextStartDT is None:
            return []  # no events in the future
        else:
            returnCalItems = []
            for calItem in self._calendarItems.copy():
                if nextStartDT == calItem.Get('Start'):
                    returnCalItems.append(calItem)
            return returnCalItems

    def RegisterCalendarItems(self, calItems, startDT, endDT):
        '''

        calItems should contain ALL the items between startDT and endDT

        :param calItems:
        :param startDT:
        :param endDT:
        :return:
        '''
        # Check for new and changed items
        for thisItem in calItems:
            itemInMemory = self.GetCalendarItemByID(thisItem.get('ItemId'))
            if itemInMemory is None:
                # this is a new item
                self._calendarItems.append(thisItem)
                if callable(self._NewCalendarItem):
                    self._NewCalendarItem(self, thisItem)

            elif itemInMemory != thisItem:
                # this item exist in memory but has somehow changed
                self._calendarItems.remove(itemInMemory)
                self._calendarItems.append(thisItem)
                if callable(self._CalendarItemChanged):
                    self._CalendarItemChanged(self, thisItem)

        # check for deleted items
        for itemInMemory in self._calendarItems.copy():
            if startDT <= itemInMemory <= endDT:
                if itemInMemory not in calItems:
                    # a event was deleted from the exchange server
                    self._calendarItems.remove(itemInMemory)
                    if callable(self._CalendarItemDeleted):
                        self._CalendarItemDeleted(self, itemInMemory)
