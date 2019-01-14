import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule, routingComponents } from './app-routing.module';
import { AppComponent } from './app.component';
import { PageNotFoundComponent } from './page-not-found/page-not-found.component';
import { HomeComponent } from './home/home.component';
import { CompetitionsDetailsComponent } from './competitions-details/competitions-details.component';
import { LoginComponent } from './login/login.component';
import { HttpClientModule } from '@angular/common/http';
import { ProtocolsComponent } from './protocols/protocols.component';
import { ProtocolsUploadComponent } from './protocols-upload/protocols-upload.component'
import {FormsModule} from "@angular/forms";
import { ProtocolsDetailsComponent } from './protocols-details/protocols-details.component';
import { ProtocolsExecutionComponent } from './protocols-execution/protocols-execution.component';
import { MainNavComponent } from './main-nav/main-nav.component';
import { LayoutModule } from '@angular/cdk/layout';
import { MatToolbarModule, MatButtonModule, MatSidenavModule, MatIconModule, MatListModule } from '@angular/material';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

@NgModule({
  declarations: [
    AppComponent,
    routingComponents,
    PageNotFoundComponent,
    HomeComponent,
    CompetitionsDetailsComponent,
    LoginComponent,
    ProtocolsComponent,
    ProtocolsUploadComponent,
    ProtocolsDetailsComponent,
    ProtocolsExecutionComponent,
    MainNavComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    LayoutModule,
    MatToolbarModule,
    MatButtonModule,
    MatSidenavModule,
    MatIconModule,
    MatListModule,
    BrowserAnimationsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }