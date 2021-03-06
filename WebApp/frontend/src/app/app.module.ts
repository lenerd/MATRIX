import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule, routingComponents } from './app-routing.module';
import { AppComponent } from './app.component';
import { PageNotFoundComponent } from './Components/page-not-found/page-not-found.component';
import { HomeComponent } from './Components/home/home.component';
import { CompetitionsDetailsComponent } from './Components/competitions-details/competitions-details.component';
import { LoginComponent } from './Components/login/login.component';
import { HttpClientModule } from '@angular/common/http';
import { ProtocolsComponent } from './Components/protocols/protocols.component';
import { ProtocolsUploadComponent } from './Components/protocols-upload/protocols-upload.component'
import {FormsModule} from "@angular/forms";
import { MainNavComponent } from './Components/main-nav/main-nav.component';
import { LayoutModule } from '@angular/cdk/layout';
import { MatToolbarModule, MatButtonModule, MatSidenavModule, MatIconModule, MatListModule, MatTableModule,
  MatPaginatorModule, MatSortModule, MatSelectModule, MatRadioModule, MatCheckboxModule } from '@angular/material';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { DeploymentComponent } from './Components/deployment/deployment.component';
import { ExecutionComponent } from './Components/execution/execution.component';
import { DeploymentResultComponent } from './Components/deployment-result/deployment-result.component';
import { ReportingComponent } from './Components/reporting/reporting.component';
import { ExecutionResultComponent } from './Components/execution-result/execution-result.component';
import { CompetitionsRegistrationComponent } from './Components/competitions-registration/competitions-registration.component';
import { ReportingResultComponent } from './Components/reporting-result/reporting-result.component';
import {AuthService} from './Services/auth.service';
import { CallbackComponent } from './Components/callback/callback.component';
import { DeploymentUpdateComponent } from './Components/deployment-update/deployment-update.component';
import {ExecutionUpdateComponent} from './Components/execution-update/execution-update.component';
import { ProtocolsUpdateComponent } from './Components/protocols-update/protocols-update.component';

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
    MainNavComponent,
    DeploymentComponent,
    DeploymentComponent,
    ExecutionComponent,
    DeploymentResultComponent,
    ReportingComponent,
    ExecutionResultComponent,
    CompetitionsRegistrationComponent,
    ReportingResultComponent,
    CallbackComponent,
    DeploymentUpdateComponent,
    ExecutionUpdateComponent,
    ProtocolsUpdateComponent
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
    BrowserAnimationsModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatSelectModule,
    MatRadioModule,
    MatCheckboxModule
  ],
  providers: [AuthService],
  bootstrap: [AppComponent]
})
export class AppModule { }
