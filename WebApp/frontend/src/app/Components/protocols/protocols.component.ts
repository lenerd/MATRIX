import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs/';
import {DataSource} from '@angular/cdk/collections';
import {DbService} from '../../Services/db.service';
import {Protocol} from '../../classes';

@Component({
  selector: 'app-protocols',
  templateUrl: './protocols.component.html',
  styleUrls: ['./protocols.component.css']
})
export class ProtocolsComponent implements OnInit {

  dataSource = new ProtocolDataSource(this.dbService);
  displayedColumns = ['name', 'security', 'threshold', 'relatedArticle', 'update', 'delete'];
  constructor(private dbService: DbService) { }

  ngOnInit() {
  }

  deleteProtocol(protocolName: string): void {
    const res = this.dbService.deleteProtocol(protocolName).subscribe(
      value =>  alert('Protocol " + protocolName + " deleted from the system'),
      error => console.log('error')
    );
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
