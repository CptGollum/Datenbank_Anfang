
class Auto:
    def __init__(self, reifen, türen, ps, baujahr):
        self.reifen = reifen
        self.türen = türen
        self.ps = ps 
        self.baujahr = baujahr

    def fahren(self):
        print('fährt')

porsche = Auto(4,4,400,2000)
print(porsche.fahren())