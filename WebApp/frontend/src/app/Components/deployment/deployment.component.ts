import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/';
import { DataSource } from '@angular/cdk/collections';
import { DbService } from '../../Services/db.service';
import { AuthService } from '../../Services/auth.service';
import { Router } from '@angular/router';
import {Protocol} from '../../classes';


@Component({
  selector: 'app-protocol-deployment',
  templateUrl: './deployment.component.html',
  styleUrls: ['./deployment.component.css']
})
export class DeploymentComponent implements OnInit {
  dataSource = new ProtocolDataSource(this.dbService);
  displayedColumns = ['name', 'action', 'update'];
  actions = ['Deploy Instance(s)', 'Create key pair(s)', 'Create security group',
    'Update network details', 'Terminate machines', 'Change machines types', 'Start instances', 'Stop instances'];

  constructor(private dbService: DbService, private auth: AuthService, private router: Router) {
    if (!localStorage.getItem('isLoggedIn')) {
      this.router.navigate(['/login']).catch(function (err) {
        if (err) {
          console.error(err);
        }
      });
    }
  }

  ngOnInit() {
  }

  onChange(operation, protocol) {
    this.router.navigate(['/deployment/' + protocol + '/' + operation]).catch(function (err) {
      if (err) {
        console.error(err);
      }
    });
  }

}

export class ProtocolDataSource extends DataSource<any> {
  constructor(private dbService: DbService) {
    super();
  }

  connect(): Observable<Protocol[]> {
    return this.dbService.getProtocols();
  }

  disconnect() {}
}
