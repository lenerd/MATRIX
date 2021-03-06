import { Component, OnInit } from '@angular/core';
import {DataSource} from '@angular/cdk//collections';
import {DbService} from '../../Services/db.service';
import {Observable} from 'rxjs';
import {Router} from '@angular/router';
import {Protocol} from '../../classes';

@Component({
  selector: 'app-reporting',
  templateUrl: './reporting.component.html',
  styleUrls: ['./reporting.component.css']
})
export class ReportingComponent implements OnInit {
  dataSource = new ReportingDataSource(this.dbService);
  displayedColumns = ['name', 'action'];
  actions = ['Analyze Results using Excel', 'Analyze Results using Elasticsearch'];

  constructor(private dbService:DbService, private router:Router)
  {
    if (!localStorage.getItem('isLoggedIn'))
      this.router.navigate(['/login']).catch(function (err) {
      if(err)
        console.error(err);
    });
  }

  ngOnInit() {
  }

  onChange(operation, protocol){
    this.router.navigate(['/reporting/' + protocol + '/' + operation]).catch(function (err) {
      if(err)
        console.error(err);
    });
  }

}

export class ReportingDataSource extends DataSource<any> {
  constructor(private dbService:DbService) {
    super()
  }

  connect(): Observable<Protocol[]> {
    return this.dbService.getProtocols();
  }

  disconnect() {}
}

