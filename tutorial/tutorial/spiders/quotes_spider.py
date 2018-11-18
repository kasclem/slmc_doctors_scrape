import os

import scrapy
from scrapy import FormRequest, Request
import re
import csv

from scrapy.http import Response


class ClinicModel():

    @staticmethod
    def extractBuilding(branch):
        pattern = r'''(no.</h4>\s+<p>)(.*?)(</p>)'''
        building = re.findall(pattern, branch, re.S)
        some = building[0][1] if len(building)==1 and len(building[0])>1 else None
        return some

    @staticmethod
    def extractSchedule(branch):
        pattern = r"(Day</h4>\s+<p>)(.*?)(</p>)"
        schedule = re.findall(pattern, branch, re.S)
        schedule = schedule[0][1] if len(schedule)==1 and len(schedule[0])>1 else None
        return schedule

    @staticmethod
    def extractNumber(branch):
        pattern = r"(Location</h4>\s+<p>)(.*?)(</p>)"
        officeNum = re.findall(pattern, branch, re.S)
        officeNum = officeNum[0][1] if len(officeNum)==1 and len(officeNum[0])>1 else None
        return officeNum

    @staticmethod
    def parseClinic(branch, schedule, isLast):
        ender = "<h4 class" if not isLast else "</div>"
        pattern = r""+branch + "</h4>.*?" + ender
        string = schedule.extract_first()
        search = re.findall(pattern, string, re.S)
        branch1 = search[0]
        building = ClinicModel.extractBuilding(branch1)
        schedule = ClinicModel.extractSchedule(branch1)
        officeNum = ClinicModel.extractNumber(branch1)
        clinic = {
            "branch":branch,
            "building-room_no":building,
            "schedule":schedule,
            "office_number":officeNum
        }
        #clinic = ClinicModel(branch, building, schedule, officeNum)
        return clinic

    @staticmethod
    def parseClinics(respo):
        clinics = []
        schedule = respo.css("div.view-schedule")
        branch_list = schedule.css("h4.sched-place.hdlight::text").extract()
        if(len(branch_list)==0):
            return []
        i = 0
        while i<len(branch_list)-1:
            branch = branch_list[i]
            clinics.append(ClinicModel.parseClinic(branch, schedule, False))
            i+=1
        clinics.append(ClinicModel.parseClinic(branch_list[i], schedule, True))
        return clinics

    def __init__(self, branch, bldg_room_no, schedule, office_number):
        self.branch = branch
        self.bldg_room_no = bldg_room_no
        self.schedule = schedule
        self.office_number = office_number


class EntryModel():
    entryModels = []

    @staticmethod
    def write_tocsv():
        with open('doctors.csv', 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            csv_writer.writerow(["Name", "Superior Surname", "Specialization", "HMO Accreditation"])
            for x in EntryModel.entryModels:
                name = x.name
                superior = x.superior
                specializations = x.specializations
                hmo_accreditations = x.hmo_accreditations
                clinics = x.clinics
                for y in specializations:
                    for z in hmo_accreditations:
                        csv_writer.writerow((name, superior, y, z))

    @staticmethod
    def parse(respo):
        name = respo.css("div.nsd h2::text").extract_first()
        superior = respo.css("div.nsd h1::text").extract_first()
        specializations = respo.css("div.specialization h4::text").extract()
        hmo_accreditations = respo.css("div ul li::text").extract()
        clinics = ClinicModel.parseClinics(respo)
        entryModel = {
            "name":name,
            "superior":superior,
            "specializations":specializations,
            "hmo_accreditations":hmo_accreditations,
            "clinics":clinics
        }
        return entryModel

    def __init__(self, name, superior, specializations, hmo_accreditations, clinics):
        self.name = name
        self.superior = superior
        #list
        self.specializations = specializations
        #list
        self.hmo_accreditations = hmo_accreditations
        #list
        self.Clinics = clinics


class DoctorSpider(scrapy.Spider):
    name = "doctors"
    start_urls = [
        'https://doctorsdirectory.stlukesmedicalcenter.com.ph/index.html',
    ]
    scraped_flag = False

    def makePost(self, size):
        form_data = {
            "size":size,
            "page":"0"
        }
        url = DoctorSpider.start_urls[0]
        return FormRequest(url, callback=DoctorSpider.parse2, formdata=form_data)

    #first parse gets the size to be submitted for pagination
    def parse(self, response):
        size = response.css('input#navInfoTotal::attr(value)').extract_first()
        if not DoctorSpider.scraped_flag:
            yield self.makePost(size)
            DoctorSpider.scraped_flag = True

    @staticmethod
    def parse2(response):
        articles = response.css("div.article")
        i=0
        for x in articles:
            i+=1
            yield EntryModel.parse(x)