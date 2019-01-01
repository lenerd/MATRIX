import {Injectable, NgModule} from '@angular/core';
import {HttpClient, HttpClientModule} from '@angular/common/http';
import { CommonModule } from '@angular/common';
import {AppComponent} from "./app.component";
import {Observable} from "rxjs";
import {ICompetition, IProtocol, IProtocolData} from "./interfaces";


@NgModule({
  imports: [CommonModule, HttpClientModule],
  exports: [],
  declarations: [ AppComponent ],
  bootstrap:    [ AppComponent ]
})

@Injectable({
  providedIn: 'root'
})
export class DbService {

  private _urlApi: string = 'http://localhost:5000/';

  constructor(private _http:HttpClient) { }

  getCompetitions(): Observable<ICompetition[]> {
    let url = this._urlApi + 'competitions';
    return this._http.get<ICompetition[]>(url);
  }

  getProtocols(): Observable<IProtocol[]> {
    let url = this._urlApi + 'protocols';
    return this._http.get<IProtocol[]>(url);
  }

  getProtocolDate(protocolName: string): Observable<IProtocolData> {
  let url = this._urlApi + 'getprotocoldata/' + protocolName;
    return this._http.get<IProtocolData>(url);
  }

  executeProtocol(protocolName: string) {
    let url = this._urlApi + 'protocols/' + protocolName;
    return this._http.get(url);
  }


}
